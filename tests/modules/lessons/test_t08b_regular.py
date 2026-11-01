"""Finite regular batches: persisted previews, recovery, concurrency, access and D04."""
import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4, UUID

import pytest
from sqlalchemy import select, func, update

from src.modules.lessons.models import Lesson, RegularLessonSeries, RegularLessonOperation
from src.modules.lesson_students.models import LessonStudent
from src.modules.lesson_students.repository import LessonStudentsRepository
from src.modules.lessons.depends import get_regular_lessons_service
from src.modules.lessons.models_dto import PreviewRegularLessonsRequestDTO, ConfirmRegularLessonsRequestDTO
from src.modules.teacher_students.models import TeacherStudent
from src.modules.student_courses.models import StudentCourse
from src.modules.users.models import User
from tests.modules.auth.test_t06_permissions import world, auth


def request(w, **overrides):
    return dict(operation_id=str(uuid4()), action='create', lesson={
        'course_id': w['courses'][0].id, 'student_user_id': w['accounts']['s1'][0].id,
        'title': 'Synthetic weekly', 'scheduled_at': '2028-12-25T15:00:00+03:00',
    }, **overrides)


async def preview(c, w, data=None, actor='t1'):
    r = await c.post('/lessons/regular/previews', headers=auth(w['accounts'][actor][1]), json=data or request(w))
    assert r.status_code == 200, r.text
    return r.json()


async def confirm(c, w, p, **overrides):
    return await c.post(f"/lessons/regular/operations/{p['operation_id']}/confirm",
        headers=auth(w['accounts']['t1'][1]), json={'preview_revision':p['preview_revision'], **overrides})


async def series(c, w, **overrides):
    p = await preview(c, w, request(w, **overrides))
    r = await confirm(c, w, p)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_default_dates_year_boundary_recovery_and_visibility(client_for_tests, world, session_db):
    c=client_for_tests; w=world; data=request(w)
    before=await session_db.scalar(select(func.count()).select_from(Lesson))
    p=await preview(c,w,data)
    assert p['preview']['count']==4 and p['preview']['timezone']=='Europe/Moscow'
    assert [x['scheduled_at'] for x in p['preview']['occurrences']]==[
        '2028-12-25T12:00:00Z','2029-01-01T12:00:00Z','2029-01-08T12:00:00Z','2029-01-15T12:00:00Z']
    assert await session_db.scalar(select(func.count()).select_from(Lesson))==before
    assert await preview(c,w,data)==p
    r=await confirm(c,w,p); assert r.status_code==200,r.text
    receipt=r.json(); assert receipt['state']=='committed'; ids=receipt['result']['lesson_ids']
    assert len(ids)==4
    assert (await confirm(c,w,p)).json()==receipt
    got=await c.get(f"/lessons/regular/operations/{p['operation_id']}",headers=auth(w['accounts']['t1'][1]))
    assert got.json()==receipt
    for lid in ids:
        rows=list((await session_db.scalars(select(LessonStudent).where(LessonStudent.lesson_id==lid))).all())
        assert len(rows)==1 and rows[0].student_id==w['students'][0].id
        own=await c.get(f'/lessons/{lid}',headers=auth(w['accounts']['s1'][1])); assert own.status_code==200
        assert own.json()['regular_series_id']==receipt['result']['series_id']
        assert (await c.get(f'/lessons/{lid}',headers=auth(w['accounts']['s2'][1]))).status_code==404
    serialized=str(receipt)
    assert 'teacher_id' not in serialized and 'student_id' not in serialized and '_versions' not in serialized


@pytest.mark.asyncio
async def test_move_cancel_extend_stop_and_explicit_cancel(client_for_tests,world,session_db):
    c=client_for_tests;w=world;h=auth(w['accounts']['t1'][1]); r=await series(c,w)
    sid=r['result']['series_id'];ids=r['result']['lesson_ids']
    moved=await c.patch(f'/lessons/{ids[0]}',headers=h,json={'scheduled_at':'2029-03-01T12:00:00Z'})
    assert moved.status_code==200,moved.text
    assert (await c.patch(f'/lessons/{ids[1]}',headers=h,json={'status':'cancelled'})).status_code==200
    p=await preview(c,w,dict(operation_id=str(uuid4()),action='extend',series_id=sid,weeks=2))
    assert [o['scheduled_at'] for o in p['preview']['occurrences']]==['2029-01-22T12:00:00Z','2029-01-29T12:00:00Z']
    ex=await confirm(c,w,p);assert ex.status_code==200,ex.text
    assert (await confirm(c,w,p)).json()==ex.json()
    assert await session_db.scalar(select(func.count()).select_from(Lesson).where(Lesson.regular_series_id==UUID(sid)))==6
    # Keep completed/archived lessons; cancellation also includes the moved first lesson.
    assert (await c.patch(f'/lessons/{ids[2]}',headers=h,json={'status':'completed'})).status_code==200
    assert (await c.delete(f'/lessons/{ids[3]}',headers=h)).status_code==200
    stop=await preview(c,w,dict(operation_id=str(uuid4()),action='stop',series_id=sid))
    stopped=await confirm(c,w,stop);assert stopped.status_code==200,stopped.text
    assert stopped.json()['result']['stopped']
    assert (await c.get(f'/lessons/{ids[0]}',headers=h)).json()['status']=='scheduled'
    bad=await c.post('/lessons/regular/previews',headers=h,json=dict(operation_id=str(uuid4()),action='extend',series_id=sid))
    assert bad.status_code==409
    p=await preview(c,w,dict(operation_id=str(uuid4()),action='cancel_future',series_id=sid))
    assert set(o['lesson_id'] for o in p['preview']['occurrences'])=={ids[0],*ex.json()['result']['lesson_ids']}
    cancelled=await confirm(c,w,p);assert cancelled.status_code==200,cancelled.text
    assert (await confirm(c,w,p)).json()==cancelled.json()
    assert (await c.get(f'/lessons/{ids[2]}',headers=h)).json()['status']=='completed'
    assert (await c.get(f'/lessons/{ids[3]}',headers=h)).json()['is_deleted']
    state=await c.get(f'/lessons/regular/series/{sid}',headers=h)
    assert state.status_code==200 and state.json()['stopped']


@pytest.mark.asyncio
async def test_new_overlap_refresh_requires_new_revision_and_ack(client_for_tests,world):
    from tests.modules.lessons.test_t08_scheduling import create
    c=client_for_tests;w=world;p=await preview(c,w)
    conflict=await create(c,w,scheduled_at='2028-12-25T12:54:00Z'); assert conflict.status_code==201
    r=await confirm(c,w,p,acknowledge_conflicts=True)
    assert r.status_code==409,r.text
    fresh=r.json()['preview'];assert fresh['preview_revision']==2
    assert fresh['preview']['occurrences'][0]['conflict_lesson_ids']==[conflict.json()['id']]
    assert (await confirm(c,w,p,acknowledge_conflicts=True)).status_code==409
    assert (await confirm(c,w,fresh)).status_code==409
    assert (await confirm(c,w,fresh,acknowledge_conflicts=True)).status_code==200


@pytest.mark.asyncio
async def test_cancel_preview_cannot_silently_cancel_moved_or_completed(client_for_tests,world):
    c=client_for_tests;w=world;receipt=await series(c,w);sid=receipt['result']['series_id'];lid=receipt['result']['lesson_ids'][0]
    p=await preview(c,w,dict(operation_id=str(uuid4()),action='cancel_future',series_id=sid))
    await c.patch(f'/lessons/{lid}',headers=auth(w['accounts']['t1'][1]),json={'status':'completed'})
    r=await confirm(c,w,p);assert r.status_code==409
    fresh=r.json()['preview'];assert fresh['preview']['count']==3
    assert (await confirm(c,w,fresh)).status_code==200
    assert (await c.get(f'/lessons/{lid}',headers=auth(w['accounts']['t1'][1]))).json()['status']=='completed'


@pytest.mark.asyncio
@pytest.mark.parametrize('condition',['ended_link','disabled','expired','revoked','archived'])
async def test_access_lost_between_preview_confirm_leaves_no_batch(client_for_tests,world,session_db,condition):
    from src.modules.courses.models import Course
    c=client_for_tests;w=world;p=await preview(c,w)
    if condition=='ended_link':
        await session_db.execute(update(TeacherStudent).where(TeacherStudent.teacher_id==w['teachers'][0].id).values(ended_at=datetime.now(UTC)))
    elif condition=='disabled':
        await session_db.execute(update(User).where(User.id==w['accounts']['s1'][0].id).values(is_active=False))
    elif condition=='archived':
        await session_db.execute(update(Course).where(Course.id==w['courses'][0].id).values(is_deleted=True))
    else:
        values={'expires_at':datetime.now(UTC)-timedelta(seconds=1)} if condition=='expired' else {'history_revoked':True}
        await session_db.execute(update(StudentCourse).where(StudentCourse.course_id==w['courses'][0].id).values(**values))
    await session_db.commit()
    r=await confirm(c,w,p); assert r.status_code in (403,404,422),r.text
    assert await session_db.scalar(select(func.count()).select_from(RegularLessonSeries))==0
    assert (await c.get(f"/lessons/regular/operations/{p['operation_id']}",headers=auth(w['accounts']['t1'][1]))).json()['state']=='preview'


@pytest.mark.asyncio
@pytest.mark.parametrize('actor,expected',[('t2',404),('s1',403),('admin',403)])
async def test_foreign_series_operation_and_create_scope(client_for_tests,world,actor,expected):
    c=client_for_tests;w=world;r=await series(c,w);h=auth(w['accounts'][actor][1]);sid=r['result']['series_id']
    for path in [f"/lessons/regular/operations/{r['operation_id']}",f'/lessons/regular/series/{sid}']:
        assert (await c.get(path,headers=h)).status_code==expected
    assert (await c.post('/lessons/regular/previews',headers=h,json=request(w))).status_code==expected
    assert (await c.post('/lessons/regular/previews',headers=h,json={'operation_id':str(uuid4()),'action':'extend','series_id':sid})).status_code==expected


@pytest.mark.asyncio
async def test_failure_middle_and_deadline_failure_roll_back_all(client_for_tests,world,session_db,monkeypatch):
    c=client_for_tests;w=world;p=await preview(c,w);n=0
    original=LessonStudentsRepository.add_student_to_lesson
    async def fail(self,data):
        nonlocal n
        n+=1
        if n==3: raise RuntimeError('synthetic middle failure')
        return await original(self,data)
    before=[await session_db.scalar(select(func.count()).select_from(m)) for m in [Lesson,LessonStudent]]
    monkeypatch.setattr(LessonStudentsRepository,'add_student_to_lesson',fail)
    with pytest.raises(RuntimeError,match='synthetic middle'):
        await confirm(c,w,p)
    assert [await session_db.scalar(select(func.count()).select_from(m)) for m in [Lesson,LessonStudent]]==before
    assert await session_db.scalar(select(func.count()).select_from(RegularLessonSeries))==0
    monkeypatch.setattr(LessonStudentsRepository,'add_student_to_lesson',original)
    from src.modules.homework_placements.service import HomeworkPlacementsService
    async def deadline_fail(*args): raise RuntimeError('synthetic deadline failure')
    with monkeypatch.context() as patch:
        patch.setattr(HomeworkPlacementsService,'recalculate_course',deadline_fail)
        with pytest.raises(RuntimeError,match='synthetic deadline'):
            await confirm(c,w,p)
    assert await session_db.scalar(select(func.count()).select_from(RegularLessonSeries))==0
    assert (await confirm(c,w,p)).status_code==200


@pytest.mark.asyncio
async def test_concurrent_confirm_extend_and_stale_separate_preview(config_fix,world):
    user_id=world['accounts']['t1'][0].id
    async def preview_service(data):
        async with config_fix.db_connection.session_local() as db:
            return await get_regular_lessons_service(db).preview_regular(user_id,PreviewRegularLessonsRequestDTO.model_validate(data))
    async def confirm_service(p):
        async with config_fix.db_connection.session_local() as db:
            return await get_regular_lessons_service(db).confirm_regular(user_id,p.operation_id,ConfirmRegularLessonsRequestDTO(preview_revision=p.preview_revision))
    payload=request(world)
    a,b=await asyncio.wait_for(asyncio.gather(preview_service(payload),preview_service(payload)),20)
    assert a==b
    a,b=await asyncio.wait_for(asyncio.gather(confirm_service(a),confirm_service(b)),20)
    assert a==b and len(a.result.lesson_ids)==4
    sid=a.result.series_id
    ext=await preview_service(dict(operation_id=str(uuid4()),action='extend',series_id=str(sid),weeks=2))
    other=await preview_service(dict(operation_id=str(uuid4()),action='extend',series_id=str(sid),weeks=2))
    a,b=await asyncio.wait_for(asyncio.gather(confirm_service(ext),confirm_service(ext)),20)
    assert a==b and len(a.result.lesson_ids)==2
    from src.modules.lessons.exception import RegularPreviewChanged
    with pytest.raises(RegularPreviewChanged) as exc:
        await confirm_service(other)
    assert exc.value.preview['preview']['occurrences'][0]['scheduled_at']=='2029-02-05T12:00:00Z'
    async with config_fix.db_connection.session_local() as db:
        assert await db.scalar(select(func.count()).select_from(Lesson).where(Lesson.regular_series_id==sid))==6


@pytest.mark.asyncio
@pytest.mark.parametrize('values',[{'weeks':0},{'weeks':13},{'weeks':True},{'weeks':1.5},{'series_id':str(uuid4())}])
async def test_invalid_batch_inputs(client_for_tests,world,values):
    r=await client_for_tests.post('/lessons/regular/previews',headers=auth(world['accounts']['t1'][1]),json=request(world,**values))
    assert r.status_code==422,r.text


@pytest.mark.asyncio
async def test_reuse_key_other_payload_and_past_overflow(client_for_tests,world):
    c=client_for_tests;w=world;data=request(w);p=await preview(c,w,data)
    data['weeks']=2
    assert (await c.post('/lessons/regular/previews',headers=auth(w['accounts']['t1'][1]),json=data)).status_code==409
    for date in ['2020-01-01T12:00:00Z','9999-12-25T12:00:00Z','2028-12-25T12:00:00']:
        data=request(w);data['lesson']['scheduled_at']=date
        r=await c.post('/lessons/regular/previews',headers=auth(w['accounts']['t1'][1]),json=data)
        assert r.status_code==422,r.text


@pytest.mark.asyncio
async def test_independent_tabs_cannot_create_same_series_twice(client_for_tests,world,session_db):
    c=client_for_tests;w=world;a=await preview(c,w);b=await preview(c,w)
    assert (await confirm(c,w,a)).status_code==200
    assert (await confirm(c,w,b,acknowledge_conflicts=True)).status_code==409
    assert (await c.post('/lessons/regular/previews',headers=auth(w['accounts']['t1'][1]),json=request(w))).status_code==409
    assert await session_db.scalar(select(func.count()).select_from(RegularLessonSeries))==1


@pytest.mark.asyncio
async def test_series_batches_recalculate_deadline_and_preserve_checked(client_for_tests,world):
    from tests.modules.homeworks.test_t11_deadlines import history
    from tests.modules.homework_submissions.test_t09_lifecycle import route
    c=client_for_tests;w=world;h=auth(w['accounts']['t1'][1]);student=auth(w['accounts']['s1'][1])
    assert (await c.patch(f"/lessons/{w['lessons'][0].id}",headers=h,json={'scheduled_at':'2028-12-20T12:00:00Z'})).status_code==200
    assert (await history(c,w))[0]['due_at'] is None
    receipt=await series(c,w);sid=receipt['result']['series_id'];ids=receipt['result']['lesson_ids']
    assert (await history(c,w))[0]['due_lesson_id']==ids[0]
    assert (await c.patch(f'/lessons/{ids[0]}',headers=h,json={'scheduled_at':'2029-03-01T12:00:00Z'})).status_code==200
    assert (await history(c,w))[0]['due_lesson_id']==ids[1]
    submitted=await c.post(route(w,'/submit'),headers=student);assert submitted.status_code==200
    reviewed=await c.patch(route(w,'/teacher'),headers=h,json={'grade':4,'expected_version':submitted.json()['version']})
    assert reviewed.status_code==200,reviewed.text
    before=await history(c,w)
    p=await preview(c,w,dict(operation_id=str(uuid4()),action='cancel_future',series_id=sid))
    assert (await confirm(c,w,p)).status_code==200
    assert await history(c,w)==before
    # Cancellation keeps original learning material and a single original answer.
    assert (await c.get(f"/lessons/{w['lessons'][0].id}",headers=student)).json()['has_homework']


@pytest.mark.asyncio
async def test_known_batch_overlap_warns_and_adjacent_does_not(client_for_tests,world):
    from tests.modules.lessons.test_t08_scheduling import create
    c=client_for_tests;w=world
    adjacent=await create(c,w,scheduled_at='2028-12-25T12:55:00Z');assert adjacent.status_code==201
    p=await preview(c,w);assert not p['preview']['occurrences'][0]['conflict_lesson_ids']
    data=request(w);data['lesson']['duration_minutes']=10081
    p=await preview(c,w,data)
    assert p['preview']['occurrences'][0]['conflict_occurrence_dates']==['2029-01-01T12:00:00Z']
    assert (await confirm(c,w,p)).status_code==409
    assert (await confirm(c,w,p,acknowledge_conflicts=True)).status_code==200


@pytest.mark.asyncio
async def test_series_archive_readonly_recovery_and_explicit_purge(client_for_tests,world,session_db):
    c=client_for_tests;w=world;r=await series(c,w);sid=r['result']['series_id'];cid=w['courses'][0].id
    assert (await c.delete(f'/courses/{cid}',headers=auth(w['accounts']['t1'][1]))).status_code==200
    assert (await c.get(f"/lessons/regular/operations/{r['operation_id']}",headers=auth(w['accounts']['t1'][1]))).json()==r
    assert (await confirm(c,w,r)).json()==r
    p=await c.post('/lessons/regular/previews',headers=auth(w['accounts']['t1'][1]),json={'operation_id':str(uuid4()),'action':'extend','series_id':sid})
    assert p.status_code==403
    purge=await c.post(f'/courses/{cid}/purge',headers=auth(w['accounts']['admin'][1]),json={'confirm_course_id':cid,'confirm_name':w['courses'][0].name})
    assert purge.status_code==200,purge.text
    assert await session_db.scalar(select(func.count()).select_from(RegularLessonSeries))==0
    assert await session_db.scalar(select(func.count()).select_from(RegularLessonOperation))==0


@pytest.mark.asyncio
@pytest.mark.parametrize('weeks',[1,12])
async def test_min_max_horizon_and_other_teacher_shared_student(client_for_tests,world,weeks):
    c=client_for_tests;w=world;first=await series(c,w,weeks=weeks)
    assert len(first['result']['lesson_ids'])==weeks
    data=request(w,weeks=weeks);data['lesson']['course_id']=w['courses'][1].id
    p=await preview(c,w,data,actor='t2')
    assert all(not x['conflict_lesson_ids'] for x in p['preview']['occurrences'])
    r=await c.post(f"/lessons/regular/operations/{p['operation_id']}/confirm",headers=auth(w['accounts']['t2'][1]),json={'preview_revision':1})
    assert r.status_code==200,r.text
    assert r.json()['result']['series_id']!=first['result']['series_id']


@pytest.mark.asyncio
async def test_preview_cancel_without_confirm_and_notification_rollback(client_for_tests,world,session_db,monkeypatch):
    from src.modules.notifications.models import Notification
    from src.modules.notifications.service import NotificationsService
    c=client_for_tests;w=world;r=await series(c,w);sid=r['result']['series_id'];ids=r['result']['lesson_ids']
    p=await preview(c,w,dict(operation_id=str(uuid4()),action='cancel_future',series_id=sid))
    assert (await c.get(f'/lessons/{ids[0]}',headers=auth(w['accounts']['t1'][1]))).json()['status']=='scheduled'
    before=await session_db.scalar(select(func.count()).select_from(Notification))
    original=NotificationsService.lesson_event;n=0
    async def fail(self,*args):
        nonlocal n
        n+=1
        if n==2: raise RuntimeError('synthetic notification failure')
        return await original(self,*args)
    with monkeypatch.context() as patch:
        patch.setattr(NotificationsService,'lesson_event',fail)
        with pytest.raises(RuntimeError,match='synthetic notification'):
            await confirm(c,w,p)
    assert await session_db.scalar(select(func.count()).select_from(Notification))==before
    assert (await c.get(f'/lessons/{ids[0]}',headers=auth(w['accounts']['t1'][1]))).json()['status']=='scheduled'
    success=await confirm(c,w,p);assert success.status_code==200,success.text
    after=await session_db.scalar(select(func.count()).select_from(Notification))
    assert after==before+4
    assert (await confirm(c,w,p)).json()==success.json()
    assert await session_db.scalar(select(func.count()).select_from(Notification))==after
