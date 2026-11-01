"""T14b: synthetic ASGI, actual PostgreSQL scopes and independent-session saves."""
import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import event, func, select, update

from tests.modules.auth.test_t06_permissions import world
from tests.modules.homework_submissions.test_t09_lifecycle import headers
from src.modules.courses.models import Course
from src.modules.lessons.models import Lesson
from src.modules.lesson_students.models import LessonStudent
from src.modules.student_courses.models import StudentCourse
from src.modules.teacher_students.models import TeacherStudent
from src.modules.homework_submissions.models import HomeworkSubmission
from src.modules.homework_placements.models import HomeworkPlacement
from src.modules.course_lifecycle.models import EnrollmentGap


async def get(c, w, path, actor='s1', **params):
    r = await c.get(path, headers=headers(w, actor), params=params)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
@pytest.mark.parametrize('actor,index,code', [('t1',0,200),('t2',0,404),('s1',0,200),
    ('s2',0,404),('admin',0,200),('t1',1,404),('s1',1,200)])
async def test_direct_details_and_file_urls(client_for_tests, world, actor, index, code):
    c,w=client_for_tests,world
    for kind,key in [('homeworks','homeworks'),('lectures','lectures')]:
        r=await c.get(f'/{kind}/{w[key][index].id}',headers=headers(w,actor))
        assert r.status_code==code,r.text
        if code!=200:
            continue
        d=r.json()
        assert d['course_id']==w['courses'][index].id
        assert d['lesson_id']==w['lessons'][index].id
        assert d['student_user_id']==w['accounts']['s1'][0].id
        assert d['teacher_user_id']==w['accounts'][f't{index+1}'][0].id
        assert d['course_name']==w['courses'][index].name and d['lesson_title']==w['lessons'][index].title
        assert d['access_mode']=='active'
        assert d['file']['id']==d['id'] and d['file']['size_bytes'] is None
        download=await c.get(d['file']['download_url'],headers=headers(w,actor))
        assert download.status_code==200 and download.headers['content-type']=='application/pdf'
        assert '/Users/' not in r.text and 'asset' not in r.text and 'PRIVATE' not in r.text
        if kind=='homeworks':
            assert d['working_submission_id']==w['submissions'][index].id
            assert d['can_submit']==(actor=='s1')
            assert d['can_review'] is False


@pytest.mark.asyncio
@pytest.mark.parametrize('state,reason', [('course','course_archived'),('lesson','lesson_archived'),
    ('ended','enrollment_ended'),('expired','access_expired'),('link','teacher_link_ended'),
    ('recipient','history_only'),('revoked','history_only'),('gap',None)])
async def test_historical_context_and_no_get_writes(client_for_tests, world, session_db, config_fix, state, reason):
    c,w=client_for_tests,world
    now=await session_db.scalar(select(func.clock_timestamp()))
    cid=w['courses'][0].id; lid=w['lessons'][0].id
    if state=='course':
        await session_db.execute(update(Course).where(Course.id==cid).values(is_deleted=True))
    elif state=='lesson':
        await session_db.execute(update(Lesson).where(Lesson.id==lid).values(is_deleted=True))
    elif state in ('ended','expired','revoked'):
        values={'access_ended_at':now} if state=='ended' else {'expires_at':now} if state=='expired' else {'history_revoked':True}
        await session_db.execute(update(StudentCourse).where(StudentCourse.course_id==cid).values(**values))
    elif state=='link':
        await session_db.execute(update(TeacherStudent).where(TeacherStudent.teacher_id==w['teachers'][0].id).values(ended_at=now))
    elif state=='recipient':
        await session_db.execute(update(LessonStudent).where(LessonStudent.id==w['recipients'][0].id).values(access_ended_at=now))
    else:
        enrollment=await session_db.scalar(select(StudentCourse).where(StudentCourse.course_id==cid))
        session_db.add(EnrollmentGap(enrollment_id=enrollment.id,started_at=now-timedelta(days=1),ended_at=now+timedelta(days=1)))
    await session_db.commit()
    sql=[]
    def record(conn,cursor,statement,params,context,many):
        sql.append(statement)
    engine=config_fix.db_connection.engine.sync_engine
    event.listen(engine,'before_cursor_execute',record)
    try:
        for kind,key in [('homeworks','homeworks'),('lectures','lectures')]:
            path=f'/{kind}/{w[key][0].id}'
            r=await c.get(path,headers=headers(w))
            if state in ('revoked','gap'):
                assert r.status_code==404
            else:
                assert r.status_code==200,r.text
                d=r.json()
                assert d['read_only_reason']==reason and d['access_mode']=='read_only'
                assert d['can_manage'] is False
                if kind=='homeworks':
                    assert not d['can_submit'] and not d['can_review']
                assert (await c.get(d['file']['download_url'],headers=headers(w))).status_code==200
            admin=await get(c,w,path,'admin')
            assert admin['can_manage'] is False
            assert (await c.get(admin['file']['download_url'],headers=headers(w,'admin'))).status_code==200
        # Each teacher keeps their own history; the other teacher's course stays active.
        if state!='gap':
            assert (await get(c,w,f'/homeworks/{w["homeworks"][0].id}','t1'))['read_only_reason']==reason
        assert (await get(c,w,f'/homeworks/{w["homeworks"][1].id}'))['access_mode']=='active'
    finally:
        event.remove(engine,'before_cursor_execute',record)
    assert not any(s.lstrip().split()[0].upper() in ('INSERT','UPDATE','DELETE') or 'FOR UPDATE' in s.upper() for s in sql)


@pytest.mark.asyncio
async def test_recipients_are_lesson_grants_with_history_and_legacy(client_for_tests,world,session_db):
    c,w=client_for_tests,world; lid=w['lessons'][0].id
    sid=w['accounts']['s1'][0].id
    session_db.add(StudentCourse(course_id=w['courses'][0].id,student_id=w['students'][1].id))
    await session_db.commit()
    path=f'/lessons/{lid}/students'
    for actor in ['s1','t1','admin']:
        data=await get(c,w,path,actor)
        assert data['total']==1 and data['items'][0]['student_user_id']==sid
        assert set(data['items'][0])=={'student_user_id','display_name','username','access_mode','read_only_reason','can_manage','school_grade'}
        assert (await get(c,w,path,actor,offset=99))['total']==1
    for actor in ['s2','t2']:
        assert (await c.get(path,headers=headers(w,actor))).status_code==404
    session_db.add(LessonStudent(lesson_id=lid,student_id=w['students'][1].id))
    await session_db.commit()
    assert (await get(c,w,path,'t1'))['total']==2
    assert (await get(c,w,path))['total']==1
    assert all(not r['can_manage'] for r in (await get(c,w,path,'t1'))['items'])
    assert not (await get(c,w,f'/lessons/{lid}','t1'))['can_manage']
    await session_db.execute(update(LessonStudent).where(LessonStudent.id==w['recipients'][0].id).values(access_ended_at=datetime.now(UTC)))
    await session_db.commit()
    assert (await get(c,w,path))['items'][0]['read_only_reason']=='history_only'


@pytest.mark.asyncio
async def test_lecture_my_filters_sort_count_and_answer_descriptor(client_for_tests,world,session_db):
    c,w=client_for_tests,world
    from src.modules.lectures.models import Lecture
    await session_db.execute(update(Lecture).values(created_at=datetime(2020,1,1,tzinfo=UTC)))
    await session_db.commit()
    a=await get(c,w,'/lectures/my',limit=1); b=await get(c,w,'/lectures/my',offset=1,limit=1)
    assert a['total']==b['total']==2 and a['items'][0]['id']>b['items'][0]['id']
    assert (await get(c,w,'/lectures/my',sort_date='asc'))['items'][0]['id']==b['items'][0]['id']
    cid=w['courses'][0].id
    assert (await get(c,w,'/lectures/my',course_id=cid))['total']==1
    await session_db.execute(update(Course).where(Course.id==cid).values(is_deleted=True)); await session_db.commit()
    assert (await get(c,w,'/lectures/my',view='archive'))['total']==1
    assert (await get(c,w,'/lectures/my',view='active'))['total']==1
    assert (await get(c,w,'/lectures/my',offset=100))['total']==2
    sub=await get(c,w,f'/submissions/{w["submissions"][0].id}',homework_id=w['homeworks'][0].id)
    file=sub['files'][0]['file']
    assert file['id']==w['files'][0].id
    assert (await c.get(file['download_url'],headers=headers(w))).status_code==200


@pytest.mark.asyncio
async def test_debts_page_latest_context_files_and_checked(client_for_tests,world,session_db):
    from tests.modules.homeworks.test_t11_deadlines import setup, lesson, debt
    c,w=client_for_tests,world
    await setup(c,w)
    target=await lesson(c,w,3)
    await session_db.execute(update(HomeworkSubmission).where(HomeworkSubmission.id==w['submissions'][0].id).values(status='submitted'))
    await session_db.commit()
    params=dict(lesson_id=target['id'],student_user_id=w['accounts']['s1'][0].id)
    path='/homeworks/available-debts'
    data=await get(c,w,path,'t1',**params)
    assert data['total']==1 and not data['items'][0]['already_added']
    assert data['items'][0]['submission_status']=='submitted'
    assert (await get(c,w,path,'t1',offset=99,**params))['total']==1
    assert (await get(c,w,path,'t2',lesson_id=w['lessons'][1].id,student_user_id=params['student_user_id']))['total']==0
    assert (await c.get(path,headers=headers(w),params=params)).status_code==403
    p=await debt(c,w,target['id'])
    data=await get(c,w,path,'t1',**params)
    assert data['total']==1 and data['items'][0]['already_added']
    detail=await get(c,w,f'/homeworks/{w["homeworks"][0].id}')
    assert detail['placement_lesson_id']==target['id'] and detail['lesson_id']==w['lessons'][0].id
    assert f'lesson_id={target["id"]}&' in detail['file']['download_url']
    assert (await c.get(detail['file']['download_url'],headers=headers(w))).status_code==200
    lesson_items=await get(c,w,'/homeworks',lesson_id=w['lessons'][0].id,student_user_id=params['student_user_id'])
    assert lesson_items[0]['placement_kind']=='original'
    await session_db.execute(update(HomeworkSubmission).where(HomeworkSubmission.id==w['submissions'][0].id).values(status='checked'))
    await session_db.commit()
    checked=await get(c,w,f'/homeworks/{w["homeworks"][0].id}')
    assert checked['access_mode']=='active' and not checked['can_submit'] and not checked['can_review']
    assert (await get(c,w,path,'t1',**params))['total']==0


@pytest.mark.asyncio
@pytest.mark.parametrize('kind',['courses','lessons'])
async def test_conditional_patch_independent_sessions(client_for_tests,world,session_db,config_fix,app_fastapi,kind):
    from httpx import AsyncClient, ASGITransport
    from src.core.database.database import get_db
    c,w=client_for_tests,world
    path=f'/{kind}/{w[kind][0].id}'
    previous=await get(c,w,path,'t1')
    field='name' if kind=='courses' else 'title'
    # Every request gets its own actual AsyncSession. Shared client fixture is not used for the race.
    async def independent_session():
        async with config_fix.db_connection.session_local() as db:
            yield db
    old=app_fastapi.dependency_overrides[get_db]
    app_fastapi.dependency_overrides[get_db]=independent_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app_fastapi),base_url='http://test') as api:
            responses=await asyncio.gather(*[api.patch(path,headers=headers(w,'t1'),json={
                field:value,'expected_updated_at':previous['updated_at']}) for value in ['Save A','Save B']])
            assert sorted(r.status_code for r in responses)==[200,409],[r.text for r in responses]
            saved=next(r.json() for r in responses if r.status_code==200)
            assert saved['updated_at']!=previous['updated_at']
            actual=(await api.get(path,headers=headers(w,'t1'))).json()
            assert actual[field]==saved[field] and actual['updated_at']==saved['updated_at']
            # Legacy omission, nullable clearing and exact microsecond timestamp remain supported.
            r=await api.patch(path,headers=headers(w,'t1'),json={'description':None,'expected_updated_at':saved['updated_at']})
            assert r.status_code==200 and r.json()['description'] is None,r.text
            assert (await api.patch(path,headers=headers(w,'t1'),json={field:'Legacy'})).status_code==200
            assert (await api.patch(path,headers=headers(w,'t1'),json={field:None})).status_code==422
            assert (await api.patch(path,headers=headers(w,'t1'),json={'expected_updated_at':'2020-01-01T00:00:00'})).status_code==422
    finally:
        app_fastapi.dependency_overrides[get_db]=old


@pytest.mark.asyncio
async def test_batch_homework_query_bound_and_openapi(client_for_tests,world,session_db,create_homework_fixture,config_fix,app_fastapi):
    from tests.modules.homeworks.fixtures.models_dto import CreateHomeworkFixtureDTO
    c,w=client_for_tests,world
    for _ in range(48):
        await create_homework_fixture(CreateHomeworkFixtureDTO(lesson_student_id=w['recipients'][0].id))
    sql=[]
    def record(conn,cursor,statement,params,context,many): sql.append(statement)
    engine=config_fix.db_connection.engine.sync_engine
    event.listen(engine,'before_cursor_execute',record)
    try:
        await get(c,w,'/homeworks/my/page',limit=20)
        count20=len(sql); sql.clear()
        data=await get(c,w,'/homeworks/my/page',limit=50)
        count50=len(sql)
    finally:
        event.remove(engine,'before_cursor_execute',record)
    assert data['total']==50 and len(data['items'])==50
    assert count50<=count20+1 and count50<20,(count20,count50)
    assert not any('FOR UPDATE' in s.upper() for s in sql)
    schema=app_fastapi.openapi()
    for name in ['HomeworkResponseDTO','LectureResponseDTO','LessonRecipientResponseDTO','FileDescriptorDTO','CoursesResponseDTO','LessonResponseDTO']:
        fields=schema['components']['schemas'][name]['properties']
        assert not {'teacher_id','student_id','lesson_student_id','original_file_path','pdf_file_path','key','download_asset_id'} & fields.keys()
    assert '/homeworks/{homework_id}' in schema['paths'] and '/lectures/{lecture_id}' in schema['paths']
    assert schema['paths']['/homeworks/my']['get']['responses']['200']['content']['application/json']['schema']['type']=='array'


@pytest.mark.asyncio
async def test_ready_asset_metadata_matches_actual_bytes(client_for_tests,world):
    from io import BytesIO
    from PIL import Image
    from src.tools.synthetic_files import pdf_bytes
    c,w=client_for_tests,world
    params=dict(lesson_id=w['lessons'][0].id,student_user_id=w['accounts']['s1'][0].id)
    image=BytesIO(); Image.new('RGB',(20,30),'white').save(image,'PNG')
    for filename,payload,mime in [('test.pdf',pdf_bytes('T14b synthetic'),'application/pdf'),
                                  ('test.png',image.getvalue(),'image/webp')]:
        response=await c.post('/lectures',headers=headers(w,'t1'),data=params,
            files={'file':(filename,payload,'application/octet-stream')})
        assert response.status_code==201,response.text
        created=response.json()
        assert created['course_id']==w['courses'][0].id
        d=await get(c,w,f'/lectures/{created["id"]}')
        file=d['file']
        assert file['mime_type']==mime and file['size_bytes']>0
        download=await c.get(file['download_url'],headers=headers(w))
        assert download.status_code==200 and download.headers['content-type']==mime
        assert len(download.content)==file['size_bytes']
        if mime=='application/pdf':
            assert download.content==payload
        assert 'asset' not in response.text and '/Users/' not in response.text


@pytest.mark.asyncio
async def test_action_flags_and_historical_attempt_do_not_claim_manage(client_for_tests,world,session_db):
    c,w=client_for_tests,world
    cid=w['courses'][0].id; lid=w['lessons'][0].id; hid=w['homeworks'][0].id
    for actor in ['s1','t1','admin']:
        course=await get(c,w,f'/courses/{cid}',actor)
        lesson=await get(c,w,f'/lessons/{lid}',actor)
        assert course['access_mode']==lesson['access_mode']=='active'
        assert course['can_manage']==lesson['can_manage']==(actor=='t1')
        assert course['can_create_lesson']==(actor=='t1')
    await session_db.execute(update(HomeworkSubmission).where(HomeworkSubmission.id==w['submissions'][0].id).values(status='submitted'))
    await session_db.commit()
    assert (await get(c,w,f'/homeworks/{hid}','t1'))['can_review']
    await session_db.execute(update(HomeworkSubmission).where(HomeworkSubmission.id==w['submissions'][0].id).values(status='checked',is_working=False))
    await session_db.commit()
    d=await get(c,w,f'/homeworks/{hid}','t1')
    assert d['working_submission_id'] is None and not d['can_manage'] and not d['can_review']
    assert (await get(c,w,f'/homeworks/{hid}'))['can_submit']


@pytest.mark.asyncio
@pytest.mark.parametrize('state', ['link', 'not_started', 'inactive'])
async def test_create_lesson_flag_cannot_borrow_other_teachers_link(client_for_tests,world,session_db,state):
    c,w=client_for_tests,world
    if state=='link':
        await session_db.execute(update(TeacherStudent).where(
            TeacherStudent.teacher_id==w['teachers'][0].id).values(ended_at=datetime.now(UTC)))
    elif state=='not_started':
        await session_db.execute(update(StudentCourse).where(StudentCourse.course_id==w['courses'][0].id)
            .values(started_at=datetime.now(UTC)+timedelta(days=1)))
    else:
        from src.modules.users.models import User
        await session_db.execute(update(User).where(User.id==w['accounts']['s1'][0].id).values(is_active=False))
    await session_db.commit()
    course=await get(c,w,f'/courses/{w["courses"][0].id}','t1')
    assert course['access_mode']=='active' and course['can_manage']
    assert course['can_create_lesson'] is False
    assert (await get(c,w,f'/courses/{w["courses"][1].id}','t2'))['can_create_lesson']==(state!='inactive')
    if state=='link':
        student=await get(c,w,f'/courses/{w["courses"][0].id}')
        assert student['read_only_reason']=='teacher_link_ended'
