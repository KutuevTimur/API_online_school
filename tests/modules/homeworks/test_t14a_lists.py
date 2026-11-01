"""T14a: real ASGI/PostgreSQL list contracts, synthetic shared-student world."""
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update, func

from tests.modules.auth.test_t06_permissions import world
from tests.modules.homework_submissions.test_t09_lifecycle import headers
from tests.modules.homeworks.fixtures.models_dto import CreateHomeworkFixtureDTO
from src.modules.courses.models import Course
from src.modules.lessons.models import Lesson, LessonStatus
from src.modules.lesson_students.models import LessonStudent
from src.modules.homeworks.models import Homework
from src.modules.homework_submissions.models import HomeworkSubmission
from src.modules.homework_placements.models import HomeworkPlacement, HomeworkDeadlineEvent
from src.modules.student_courses.models import StudentCourse
from src.modules.teacher_students.models import TeacherStudent
from src.modules.course_lifecycle.models import EnrollmentGap


async def page(client, w, path='/homeworks/my/page', actor='s1', **params):
    r = await client.get(path, headers=headers(w, actor), params=params)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_twenty_seven_tied_homeworks_pages_count_filters_and_legacy(
        client_for_tests, world, session_db, create_homework_fixture):
    c, w = client_for_tests, world
    for _ in range(25):
        await create_homework_fixture(CreateHomeworkFixtureDTO(lesson_student_id=w['recipients'][0].id))
    await session_db.execute(update(Homework).values(created_at=datetime(2020, 1, 1, tzinfo=UTC)))
    await session_db.commit()
    a = await page(c,w); b = await page(c,w,offset=20)
    ids = [h['id'] for h in a['items'] + b['items']]
    assert a['total'] == b['total'] == 27 and len(a['items']) == 20 and len(b['items']) == 7
    assert ids == sorted(set(ids), reverse=True)
    assert (await page(c,w,offset=10000)) == dict(items=[],total=27,limit=20,offset=10000)
    assert (await page(c,w,course_id=w['courses'][0].id))['total'] == 26
    assert (await page(c,w,course_id=999999))['total'] == 0
    assert (await page(c,w,actor='s2'))['total'] == 0
    assert (await page(c,w,status='todo'))['total'] == 27
    assert (await page(c,w,overdue_only=True))['total'] == 0  # null journal deadline
    r = await c.get('/homeworks/my',headers=headers(w))
    assert r.status_code == 200 and isinstance(r.json(),list) and len(r.json()) == 27
    for actor in ['t1','t2','admin']:
        assert (await c.get('/homeworks/my/page',headers=headers(w,actor))).status_code == 403
    session_db.add_all([HomeworkSubmission(homework_id=hid,attempt_number=1,status='submitted')
                        for hid in ids[:21]])
    await session_db.commit()
    todo=await page(c,w,status='todo')
    submitted=await page(c,w,status='submitted')
    assert todo['total']==6 and len(todo['items'])==6
    assert submitted['total']==21 and len(submitted['items'])==20
    assert len((await page(c,w,status='submitted',offset=20))['items'])==1


@pytest.mark.asyncio
@pytest.mark.parametrize('status,expected', [('todo',0),('submitted',1),('checked',1),('all',2)])
async def test_working_status_and_overdue(client_for_tests,world,session_db,status,expected):
    c,w=client_for_tests,world
    await session_db.execute(update(HomeworkSubmission).where(
        HomeworkSubmission.id==w['submissions'][0].id).values(status='submitted'))
    await session_db.execute(update(HomeworkSubmission).where(
        HomeworkSubmission.id==w['submissions'][1].id).values(status='checked'))
    past=datetime.now(UTC)-timedelta(days=1)
    await session_db.execute(update(HomeworkDeadlineEvent).values(due_at=past))
    await session_db.commit()
    result=await page(c,w,status=status)
    assert result['total']==expected
    overdue=await page(c,w,overdue_only=True)
    assert overdue['total']==1 and overdue['items'][0]['id']==w['homeworks'][0].id
    assert overdue['items'][0]['submission_status']=='submitted'
    # A historical checked attempt cannot replace the current submitted answer.
    session_db.add(HomeworkSubmission(homework_id=w['homeworks'][0].id,
        attempt_number=2, is_working=False, status='checked'))
    await session_db.commit()
    assert (await page(c,w,status='submitted'))['total']==1
    assert (await page(c,w,status='checked'))['total']==1


@pytest.mark.asyncio
@pytest.mark.parametrize('state', ['course_archive','lesson_archive','ended','expired','link_ended','recipient_ended','revoked','gap'])
async def test_active_archive_history_complement_and_teacher_admin(
        client_for_tests,world,session_db,state):
    c,w=client_for_tests,world
    now=await session_db.scalar(select(func.clock_timestamp()))
    # Historical records precede the cutoff; gap removes only records in that gap.
    if state=='course_archive':
        await session_db.execute(update(Course).where(Course.id==w['courses'][0].id).values(is_deleted=True))
    elif state=='lesson_archive':
        await session_db.execute(update(Lesson).where(Lesson.id==w['lessons'][0].id).values(is_deleted=True))
    elif state in ['ended','expired','revoked']:
        values={'access_ended_at':now} if state=='ended' else {'expires_at':now} if state=='expired' else {'history_revoked':True}
        await session_db.execute(update(StudentCourse).where(StudentCourse.course_id==w['courses'][0].id).values(**values))
    elif state=='link_ended':
        await session_db.execute(update(TeacherStudent).where(TeacherStudent.teacher_id==w['teachers'][0].id).values(ended_at=now))
    elif state=='recipient_ended':
        await session_db.execute(update(LessonStudent).where(LessonStudent.id==w['recipients'][0].id).values(access_ended_at=now))
    elif state=='gap':
        enrollment=await session_db.scalar(select(StudentCourse).where(StudentCourse.course_id==w['courses'][0].id))
        session_db.add(EnrollmentGap(enrollment_id=enrollment.id,started_at=now-timedelta(days=1),ended_at=now+timedelta(days=1)))
    await session_db.commit()
    for path in ['/courses','/lessons','/homeworks/my/page']:
        all_=await page(c,w,path)
        active=await page(c,w,path,view='active')
        archive=await page(c,w,path,view='archive')
        assert all_['total']==active['total']+archive['total']
        assert {i['id'] for i in active['items']}.isdisjoint(i['id'] for i in archive['items'])
        hidden=state=='revoked' or (state=='gap' and path!='/courses')
        archived=(state!='gap' and not hidden and not (path=='/courses' and state in ['lesson_archive','recipient_ended']))
        assert all_['total']==(1 if hidden else 2),(state,path,all_)
        assert archive['total']==int(archived),(state,path,archive)
    for actor in ['t1','admin']:
        for path in ['/courses','/lessons']:
            active=await page(c,w,path,actor,view='active')
            archive=await page(c,w,path,actor,view='archive')
            physical=state=='course_archive' or (state=='lesson_archive' and path=='/lessons')
            assert archive['total']==int(physical)
            assert active['total']==(1 if actor=='t1' else 2)-int(physical)
            filtered=await page(c,w,path,actor,student_user_id=w['accounts']['s1'][0].id)
            assert filtered['total']==(1 if actor=='t1' else 2)


@pytest.mark.asyncio
async def test_student_filters_role_scope_and_deterministic_sort(client_for_tests,world,session_db):
    c,w=client_for_tests,world
    sid=w['accounts']['s1'][0].id
    await session_db.execute(update(Course).values(created_at=datetime(2020,1,1,tzinfo=UTC)))
    await session_db.execute(update(Lesson).values(scheduled_at=datetime(2020,1,1,tzinfo=UTC),status=LessonStatus.CANCELLED))
    await session_db.commit()
    for path in ['/courses','/lessons']:
        for actor,total in [('admin',2),('t1',1),('t2',1),('s1',2),('s2',0)]:
            params={} if actor=='s2' else {'student_user_id':sid}
            data=await page(c,w,path,actor,view='active',**params)
            assert data['total']==total
            assert [i['id'] for i in data['items']]==sorted([i['id'] for i in data['items']],reverse=True)
            assert (await page(c,w,path,actor,offset=1000))['items']==[]
        r=await c.get(path,headers=headers(w),params={'student_user_id':w['accounts']['s2'][0].id})
        assert r.status_code==403
        assert (await page(c,w,path,'t1',student_user_id=w['accounts']['s2'][0].id))['total']==0
    for path in ['/courses','/lessons']:
        first=await page(c,w,path,limit=1)
        second=await page(c,w,path,limit=1,offset=1)
        assert first['total']==second['total']==2
        assert first['items'][0]['id']>second['items'][0]['id']
    assert (await page(c,w,'/lessons',from_date='2021-01-01T00:00:00Z'))['total']==0
    assert (await page(c,w,'/lessons',to_date='2021-01-01T00:00:00Z'))['total']==2
    a=await page(c,w,'/lessons',sort_date='asc')
    assert [i['id'] for i in a['items']]==sorted(i['id'] for i in a['items'])
    assert (await page(c,w,'/lessons',status='completed'))['total']==0
    assert (await page(c,w,'/lessons',status='cancelled',view='active'))['total']==2
    assert (await page(c,w,'/courses','t1',my_courses=False))['total']==1
    assert (await page(c,w,'/courses','t1',teacher_user_id=w['accounts']['t2'][0].id))['total']==0


@pytest.mark.asyncio
@pytest.mark.parametrize('path,params', [
    ('/courses',{'view':'invalid'}),('/lessons',{'view':'invalid'}),
    ('/homeworks/my/page',{'view':'invalid'}),('/homeworks/my/page',{'status':'draft'}),
    *[(p,{k:v}) for p in ['/courses','/lessons','/homeworks/my/page'] for k,v in [('limit',0),('offset',-1)]],
    ('/homeworks/my/page',{'limit':101}),('/homeworks/my/page',{'overdue_only':'invalid'})])
async def test_invalid_query_422(client_for_tests,world,path,params):
    r=await client_for_tests.get(path,headers=headers(world),params=params)
    assert r.status_code==422,r.text


@pytest.mark.asyncio
async def test_latest_visible_debt_and_journal_filter_before_page(client_for_tests,world,session_db):
    from tests.modules.homeworks.test_t11_deadlines import setup, lesson, debt
    c,w=client_for_tests,world
    await setup(c,w)
    second=await lesson(c,w,3)
    p=await debt(c,w,second['id'])
    result=await page(c,w,course_id=w['courses'][0].id)
    assert result['total']==1 and result['items'][0]['placement_id']==p['id']
    assert result['items'][0]['placement_kind']=='debt'
    cutoff=datetime.now(UTC)
    past=cutoff-timedelta(days=1)
    original=await session_db.scalar(select(HomeworkPlacement).where(
        HomeworkPlacement.homework_id==w['homeworks'][0].id,HomeworkPlacement.kind=='original'))
    await session_db.execute(update(HomeworkDeadlineEvent).where(
        HomeworkDeadlineEvent.placement_id==original.id).values(due_at=past))
    # A later hidden journal snapshot must not alter either overdue filter or response.
    session_db.add(HomeworkDeadlineEvent(placement_id=original.id,
        lesson_student_id=w['recipients'][0].id, due_at=cutoff+timedelta(days=10),
        reason='synthetic_hidden',created_at=cutoff+timedelta(seconds=2)))
    await session_db.execute(update(HomeworkPlacement).where(HomeworkPlacement.id==p['id']).values(
        created_at=cutoff+timedelta(seconds=1)))
    await session_db.execute(update(StudentCourse).where(StudentCourse.course_id==w['courses'][0].id).values(
        access_ended_at=cutoff))
    await session_db.commit()
    result=await page(c,w,course_id=w['courses'][0].id,view='archive',overdue_only=True)
    assert result['total']==1
    item=result['items'][0]
    assert item['placement_id']==original.id and item['placement_kind']=='original'
    assert datetime.fromisoformat(item['deadline'].replace('Z','+00:00'))==past
    assert (await page(c,w,course_id=w['courses'][0].id,view='active'))['total']==0
    assert (await page(c,w,course_id=w['courses'][0].id,offset=100,overdue_only=True))['total']==1


@pytest.mark.asyncio
async def test_historical_checked_without_working_answer_is_todo(client_for_tests,world,session_db):
    w=world
    await session_db.execute(update(HomeworkSubmission).where(
        HomeworkSubmission.id==w['submissions'][0].id).values(status='checked',is_working=False))
    await session_db.commit()
    data=await page(client_for_tests,w,status='todo',course_id=w['courses'][0].id)
    assert data['total']==1 and data['items'][0]['submission_status'] is None
    assert (await page(client_for_tests,w,status='checked',course_id=w['courses'][0].id))['total']==0


@pytest.mark.asyncio
async def test_page_and_count_keep_snapshot_during_concurrent_insert(world,session_db,config_fix,monkeypatch):
    from src.modules.base.list_query import ListView
    from src.modules.homeworks.models_dto import HomeworkListStatus
    from src.modules.homeworks.repository import HomeworksRepository
    from src.modules.homework_placements.service import HomeworkPlacementsService
    from src.modules.users.models import User

    actor=await session_db.get(User,world['accounts']['s1'][0].id)
    execute=session_db.execute
    inserted=False

    async def insert_after_read(stmt,*args,**kwargs):
        nonlocal inserted
        result=await execute(stmt,*args,**kwargs)
        if not inserted:
            inserted=True
            # Commit on an independent connection at the first read boundary.
            async with config_fix.db_connection.session_local() as writer:
                h=Homework(lesson_student_id=world['recipients'][0].id,title='Concurrent synthetic')
                writer.add(h)
                await writer.flush()
                await HomeworkPlacementsService(writer).original(h)
                await writer.commit()
        return result

    with monkeypatch.context() as patch:
        patch.setattr(session_db,'execute',insert_after_read)
        rows,total=await HomeworksRepository(session_db).student_page(
            actor,100,0,None,HomeworkListStatus.ALL,ListView.ALL,False)
    assert inserted and len(rows)==total==2
    rows,total=await HomeworksRepository(session_db).student_page(
        actor,100,0,None,HomeworkListStatus.ALL,ListView.ALL,False)
    assert len(rows)==total==3


@pytest.mark.asyncio
async def test_openapi_additive_contract(app_fastapi):
    paths=app_fastapi.openapi()['paths']
    assert paths['/homeworks/my']['get']['responses']['200']['content']['application/json']['schema']['type']=='array'
    for path in ['/courses','/lessons','/homeworks/my/page']:
        params={p['name']:p for p in paths[path]['get']['parameters']}
        assert params['view']['schema']['default']=='all'
    assert next(p for p in paths['/courses']['get']['parameters'] if p['name']=='my_courses')['deprecated'] is True
    params={p['name']:p for p in paths['/homeworks/my/page']['get']['parameters']}
    assert params['limit']['schema']['default']==20 and params['limit']['schema']['maximum']==100


@pytest.mark.asyncio
async def test_expiry_uses_statement_time_in_existing_read_transaction(world,session_db,config_fix):
    from src.modules.courses.repository import CourseRepository
    from src.modules.check_permission.repository import course_scope, course_active_scope
    from src.modules.users.models import UserRole

    # Start a read transaction before expiry is set by an independent writer.
    started=await session_db.scalar(select(func.now()))
    async with config_fix.db_connection.session_local() as writer:
        cutoff=await writer.scalar(select(func.clock_timestamp()))
        assert cutoff>started
        await writer.execute(update(StudentCourse).where(
            StudentCourse.course_id==world['courses'][0].id).values(expires_at=cutoff))
        await writer.commit()
    uid=world['accounts']['s1'][0].id
    rows,total=await CourseRepository(session_db).get_all_courses(
        include_deleted=True,access_scope=course_scope(uid,UserRole.STUDENT)
        & course_active_scope(uid,UserRole.STUDENT))
    assert total==len(rows)==1 and rows[0].id==world['courses'][1].id


@pytest.mark.asyncio
async def test_checked_page_uses_review_time_before_homework_creation(client_for_tests, world, session_db):
    """My day must show the latest review, including reviews of older homework."""
    w = world
    now = datetime.now(UTC)
    for index, submission in enumerate(w['submissions']):
        await session_db.execute(update(HomeworkSubmission).where(
            HomeworkSubmission.id == submission.id).values(status='checked',
            checked_at=now - timedelta(days=index), grade=0))
    await session_db.execute(update(Homework).where(Homework.id == w['homeworks'][0].id)
        .values(created_at=now - timedelta(days=10)))
    await session_db.commit()
    result = await page(client_for_tests, w, status='checked', limit=1)
    assert result['total'] == 2
    assert result['items'][0]['id'] == w['homeworks'][0].id
    second = await page(client_for_tests, w, status='checked', limit=1, offset=1)
    assert second['items'][0]['id'] == w['homeworks'][1].id
