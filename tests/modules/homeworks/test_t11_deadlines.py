"""T11 real PostgreSQL API acceptance; every schedule mutation uses public API."""
import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from tests.modules.auth.test_t06_permissions import world
from tests.modules.homework_submissions.test_t09_lifecycle import headers, route
from src.modules.homework_placements.models import HomeworkPlacement, HomeworkDeadlineEvent
from src.modules.homework_placements.service import HomeworkPlacementsService
from src.modules.homeworks.models import Homework
from src.modules.homework_submissions.models import HomeworkSubmission
from src.modules.homework_submissions.depends import get_homework_submissions_service
from src.modules.homework_submissions.models_dto import UpdateSubmissionTeacherRequestDTO
from src.modules.lessons.depends import get_lessons_service
from src.modules.lessons.models_dto import UpdateLessonRequestDTO
from src.modules.lessons.models import Lesson
from src.modules.lesson_students.models import LessonStudent
from src.modules.student_courses.models import StudentCourse

BASE = datetime(2026, 10, 19, 12, tzinfo=UTC)


def iso(value):
    return datetime.fromisoformat(value.replace('Z', '+00:00')) if value else None


async def setup(client, w):
    r = await client.patch(f"/lessons/{w['lessons'][0].id}", headers=headers(w, 't1'),
                           json={'scheduled_at': BASE.isoformat()})
    assert r.status_code == 200, r.text


async def lesson(client, w, days, index=0, **extra):
    payload = dict(course_id=w['courses'][index].id, title='T11 synthetic lesson',
                   scheduled_at=(BASE + timedelta(days=days)).isoformat(), **extra)
    r = await client.post('/lessons', headers=headers(w, f't{index+1}'), json=payload)
    assert r.status_code == 201, r.text
    return r.json()


async def history(client, w, actor='s1', index=0):
    r = await client.get(f"/homeworks/{w['homeworks'][index].id}/placements", headers=headers(w, actor))
    assert r.status_code == 200, r.text
    return r.json()


async def debt(client, w, lesson_id, actor='t1', expected=201):
    r = await client.post(f"/homeworks/{w['homeworks'][0].id}/debts", headers=headers(w, actor),
                          json={'lesson_id': lesson_id})
    assert r.status_code == expected, r.text
    return r.json()


@pytest.mark.asyncio
async def test_no_next_insert_move_cancel_restore_and_passed_time(client_for_tests, world):
    c, w = client_for_tests, world
    await setup(c, w)
    assert (await history(c, w))[0]['due_at'] is None
    # Another teacher/course of this same student cannot move the deadline.
    await lesson(c, w, 1, index=1)
    assert (await history(c, w))[0]['due_at'] is None
    later = await lesson(c, w, 7)
    p = (await history(c, w))[0]
    assert iso(p['due_at']) == BASE + timedelta(days=7) and p['due_lesson_id'] == later['id']
    earlier = await lesson(c, w, 3)
    assert iso((await history(c, w))[0]['due_at']) == BASE + timedelta(days=3)
    r = await c.patch(f"/lessons/{earlier['id']}", headers=headers(w, 't1'),
                      json={'scheduled_at': (BASE+timedelta(days=8)).isoformat()})
    assert r.status_code == 200
    assert (await history(c, w))[0]['due_lesson_id'] == later['id']
    r = await c.patch(f"/lessons/{later['id']}", headers=headers(w, 't1'), json={'status': 'cancelled'})
    assert r.status_code == 200
    assert (await history(c, w))[0]['due_lesson_id'] == earlier['id']
    r = await c.delete(f"/lessons/{earlier['id']}", headers=headers(w, 't1'))
    assert r.status_code == 200
    assert (await history(c, w))[0]['due_at'] is None
    r = await c.post(f"/lessons/{earlier['id']}/restore", headers=headers(w, 'admin'))
    assert r.status_code == 200, r.text
    assert (await history(c, w))[0]['due_lesson_id'] == earlier['id']
    # Both the origin and next lesson can be in the past: completed remains a deadline.
    r = await c.patch(f"/lessons/{earlier['id']}", headers=headers(w, 't1'),
                      json={'scheduled_at': (BASE-timedelta(days=100)).isoformat(), 'status': 'completed'})
    assert r.status_code == 200
    r = await c.patch(f"/lessons/{w['lessons'][0].id}", headers=headers(w, 't1'),
                      json={'scheduled_at': (BASE-timedelta(days=101)).isoformat()})
    assert r.status_code == 200
    p = (await history(c, w))[0]
    assert iso(p['due_at']) == BASE-timedelta(days=100)
    assert len(p['events']) >= 7 and p['events'][0]['reason'] == 'assigned'
    assert (await c.post(route(w, '/submit'), headers=headers(w))).status_code == 200


@pytest.mark.asyncio
async def test_debt_same_answer_latest_and_each_lesson_history(client_for_tests, world, session_db):
    c,w=client_for_tests,world
    await setup(c,w)
    second=await lesson(c,w,3); third=await lesson(c,w,7); fourth=await lesson(c,w,10)
    p1=await debt(c,w,second['id']); p2=await debt(c,w,third['id'])
    assert p1['homework_id'] == p2['homework_id'] == w['homeworks'][0].id
    assert iso(p1['due_at']) == BASE+timedelta(days=7)
    assert p2['due_lesson_id'] == fourth['id']
    assert (await debt(c,w,third['id']))['id'] == p2['id']
    r=await c.get('/homeworks/my',headers=headers(w))
    items=[h for h in r.json() if h['id']==w['homeworks'][0].id]
    assert len(items)==1 and items[0]['placement_id']==p2['id'] and items[0]['placement_kind']=='debt'
    for lid,expected in [(w['lessons'][0].id,second['id']),(second['id'],third['id']),(third['id'],fourth['id'])]:
        r=await c.get('/homeworks',headers=headers(w),params={'lesson_id':lid,'student_user_id':w['accounts']['s1'][0].id})
        assert r.status_code==200 and r.json()[0]['due_lesson_id']==expected,r.text
        r=await c.get(f'/lessons/{lid}',headers=headers(w))
        assert r.json()['has_homework'] is True
    r=await c.get(f"/homeworks/{w['homeworks'][0].id}/file",headers=headers(w),
                  params={'lesson_id':third['id'],'student_user_id':w['accounts']['s1'][0].id})
    assert r.status_code==200 and r.content.startswith(b'%PDF')
    assert await session_db.scalar(select(func.count()).select_from(HomeworkSubmission).where(
        HomeworkSubmission.homework_id==w['homeworks'][0].id)) == 1
    await session_db.rollback()
    assert (await c.post(route(w,'/submit'),headers=headers(w))).status_code==200
    r=await c.get('/submissions/review-queue',headers=headers(w,'t1'))
    assert r.json()['total']==1
    p=await debt(c,w,fourth['id']); assert p['due_at'] is None


@pytest.mark.asyncio
@pytest.mark.parametrize('actor,code',[('t2',404),('s2',403),('s1',403),('admin',403)])
async def test_debt_actor_boundaries(client_for_tests,world,actor,code):
    c,w=client_for_tests,world
    await setup(c,w); target=await lesson(c,w,3)
    await debt(c,w,target['id'],actor,code)
    r=await c.get(f"/homeworks/{w['homeworks'][0].id}/placements",headers=headers(w,actor))
    assert r.status_code == (404 if actor in ['s2','t2'] else 200)


@pytest.mark.asyncio
async def test_debt_invalid_course_earlier_same_and_other_student(client_for_tests,world,session_db):
    c,w=client_for_tests,world
    await setup(c,w)
    await debt(c,w,w['lessons'][0].id,expected=409)
    earlier=await lesson(c,w,-1); await debt(c,w,earlier['id'],expected=409)
    other=await lesson(c,w,3,index=1); await debt(c,w,other['id'],expected=404)
    target=await lesson(c,w,3)
    await session_db.execute(update(LessonStudent).where(LessonStudent.lesson_id==target['id']).values(student_id=w['students'][1].id))
    await session_db.commit()
    await debt(c,w,target['id'],expected=404)


@pytest.mark.asyncio
async def test_same_timestamp_uses_id_and_insertion_is_deterministic(client_for_tests,world):
    c,w=client_for_tests,world
    await setup(c,w)
    a=await lesson(c,w,0); b=await lesson(c,w,0)
    assert a['id']<b['id']
    assert (await history(c,w))[0]['due_lesson_id']==a['id']
    await debt(c,w,a['id'])
    assert (await history(c,w))[-1]['due_lesson_id']==b['id']
    await debt(c,w,w['lessons'][0].id,expected=409)


@pytest.mark.asyncio
async def test_checked_freezes_every_placement_and_delete_is_forbidden(client_for_tests,world):
    c,w=client_for_tests,world
    await setup(c,w); second=await lesson(c,w,3); third=await lesson(c,w,7)
    await debt(c,w,second['id'])
    r=await c.post(route(w,'/submit'),headers=headers(w)); version=r.json()['version']
    r=await c.patch(route(w,'/teacher'),headers=headers(w,'t1'),json={'grade':4,'expected_version':version})
    assert r.status_code==200,r.text
    before=await history(c,w)
    assert all(p['frozen'] for p in before)
    await c.patch(f"/lessons/{third['id']}",headers=headers(w,'t1'),json={'scheduled_at':(BASE+timedelta(days=8)).isoformat()})
    await c.delete(f"/lessons/{second['id']}",headers=headers(w,'t1'))
    assert await history(c,w)==before
    await debt(c,w,third['id'],expected=409)
    r=await c.delete(f"/homeworks/{w['homeworks'][0].id}",headers=headers(w,'t1'),
        params={'lesson_id':w['lessons'][0].id,'student_user_id':w['accounts']['s1'][0].id})
    assert r.status_code==409


@pytest.mark.asyncio
async def test_creation_automatic_and_manual_deadline_rejected(client_for_tests,world):
    c,w=client_for_tests,world
    await setup(c,w); nxt=await lesson(c,w,3)
    data={'lesson_id':w['lessons'][0].id,'student_user_id':w['accounts']['s1'][0].id,'title':'Automatic deadline'}
    r=await c.post('/homeworks',headers=headers(w,'t1'),data={**data,'deadline':BASE.isoformat()})
    assert r.status_code==422
    r=await c.post('/homeworks',headers=headers(w,'t1'),data=data)
    assert r.status_code==201,r.text
    assert iso(r.json()['deadline'])==BASE+timedelta(days=3) and r.json()['due_lesson_id']==nxt['id']


@pytest.mark.asyncio
@pytest.mark.parametrize('operation',['move','debt','review'])
async def test_atomic_failure_rolls_back_schedule_placement_and_journal(client_for_tests,world,monkeypatch,operation):
    c,w=client_for_tests,world
    await setup(c,w); nxt=await lesson(c,w,3)
    if operation=='review':
        assert (await c.post(route(w,'/submit'),headers=headers(w))).status_code==200
    before=await history(c,w)
    async def fail(*args,**kwargs): raise RuntimeError('T11 synthetic commit failure')
    monkeypatch.setattr(AsyncSession,'commit',fail)
    with pytest.raises(RuntimeError,match='T11 synthetic'):
        if operation=='move':
            await c.patch(f"/lessons/{nxt['id']}",headers=headers(w,'t1'),json={'scheduled_at':(BASE+timedelta(days=8)).isoformat()})
        elif operation=='debt': await debt(c,w,nxt['id'])
        else: await c.patch(route(w,'/teacher'),headers=headers(w,'t1'),json={'grade':4,'expected_version':2})
    monkeypatch.undo()
    assert await history(c,w)==before
    assert iso((await c.get(f"/lessons/{nxt['id']}",headers=headers(w))).json()['scheduled_at'])==BASE+timedelta(days=3)


@pytest.mark.asyncio
@pytest.mark.parametrize('first',['move','check'])
async def test_move_vs_check_independent_sessions(config_fix,client_for_tests,world,first):
    c,w=client_for_tests,world
    await setup(c,w); nxt=await lesson(c,w,3)
    assert (await c.post(route(w,'/submit'),headers=headers(w))).status_code==200
    hid,sid=w['homeworks'][0].id,w['submissions'][0].id
    async def run(action):
        async with config_fix.db_connection.session_local() as session:
            if action=='move':
                return await get_lessons_service(session=session).update_lesson(w['accounts']['t1'][0].id,nxt['id'],
                    UpdateLessonRequestDTO(scheduled_at=BASE+timedelta(days=8)))
            return await get_homework_submissions_service(session=session,config=config_fix).update_submission_teacher(
                w['accounts']['t1'][0].id,hid,sid,UpdateSubmissionTeacherRequestDTO(grade=4,expected_version=2))
    await asyncio.wait_for(asyncio.gather(run(first),run('check' if first=='move' else 'move')),timeout=20)
    p=(await history(c,w))[0]
    assert p['frozen'] is True and p['events'][-1]['reason']=='checked'
    assert iso(p['due_at']) in [BASE+timedelta(days=3),BASE+timedelta(days=8)]
    reasons=[e['reason'] for e in p['events']]
    # A schedule update after checking cannot change the snapshot.
    if iso(p['due_at'])==BASE+timedelta(days=8): assert reasons[-2]=='lesson_updated'
    else: assert reasons[-2]!='lesson_updated' or iso(p['events'][-2]['due_at'])==BASE+timedelta(days=3)
    await c.patch(f"/lessons/{nxt['id']}",headers=headers(w,'t1'),json={'scheduled_at':(BASE+timedelta(days=9)).isoformat()})
    assert (await history(c,w))[0]==p


@pytest.mark.asyncio
async def test_cutoff_hides_later_debt_and_journal(client_for_tests,world,session_db):
    c,w=client_for_tests,world
    await setup(c,w); second=await lesson(c,w,3)
    cutoff=datetime.now(UTC)
    from src.modules.homework_placements.models import HomeworkPlacement, HomeworkDeadlineEvent
    from sqlalchemy import func
    last_event = await session_db.scalar(select(func.max(HomeworkDeadlineEvent.id))) or 0
    await debt(c,w,second['id'])
    third=await lesson(c,w,7)
    # Explicit synthetic times: PostgreSQL now() uses the transaction start.
    await session_db.execute(update(HomeworkPlacement).where(
        HomeworkPlacement.homework_id == w['homeworks'][0].id, HomeworkPlacement.kind == 'debt')
        .values(created_at=cutoff+timedelta(seconds=1)))
    await session_db.execute(update(HomeworkDeadlineEvent).where(HomeworkDeadlineEvent.id > last_event)
        .values(created_at=cutoff+timedelta(seconds=1)))
    # Emulate access ending before the debt was placed; origin still readable.
    await session_db.execute(update(StudentCourse).where(StudentCourse.course_id==w['courses'][0].id)
                             .values(access_ended_at=cutoff,is_deleted=True))
    await session_db.commit()
    p=await history(c,w)
    assert len(p)==1 and p[0]['kind']=='original'
    assert all(iso(e['created_at'])<=cutoff for e in p[0]['events'])
    r=await c.get('/homeworks/my',headers=headers(w))
    hw=next(h for h in r.json() if h['id']==w['homeworks'][0].id)
    assert hw['placement_kind']=='original' and iso(hw['deadline'])==BASE+timedelta(days=3)
    await debt(c,w,third['id'],expected=403)


@pytest.mark.asyncio
async def test_same_teacher_other_course_rejected_and_other_student_not_candidate(
    client_for_tests,world,session_db,create_course_fixture):
    from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO
    c,w=client_for_tests,world
    await setup(c,w)
    other=await create_course_fixture(CreateCourseFixtureDTO(teacher_id=w['teachers'][0].id))
    session_db.add(StudentCourse(course_id=other.id,student_id=w['students'][0].id))
    await session_db.commit()
    r=await c.post('/lessons',headers=headers(w,'t1'),json={'course_id':other.id,'title':'Other course',
                                                        'scheduled_at':(BASE+timedelta(days=1)).isoformat()})
    assert r.status_code==201,r.text
    await debt(c,w,r.json()['id'],expected=409)
    assert (await history(c,w))[0]['due_at'] is None
    target=await lesson(c,w,2)
    await session_db.execute(update(LessonStudent).where(LessonStudent.lesson_id==target['id'])
                             .values(student_id=w['students'][1].id))
    await session_db.commit()
    own=await lesson(c,w,5)
    assert (await history(c,w))[0]['due_lesson_id']==own['id']


@pytest.mark.asyncio
async def test_recipient_unlink_removes_candidate_and_preserves_history(client_for_tests,world):
    c,w=client_for_tests,world
    await setup(c,w); target=await lesson(c,w,3); later=await lesson(c,w,7)
    r=await c.delete(f"/lessons/{target['id']}/students/{w['accounts']['s1'][0].id}",headers=headers(w,'t1'))
    assert r.status_code==200,r.text
    p=(await history(c,w))[0]
    assert p['due_lesson_id']==later['id'] and p['events'][-1]['reason']=='recipient_removed'


@pytest.mark.asyncio
async def test_concurrent_identical_debt_is_idempotent(config_fix,client_for_tests,world):
    c,w=client_for_tests,world
    await setup(c,w); nxt=await lesson(c,w,3)
    async def run():
        async with config_fix.db_connection.session_local() as session:
            return await HomeworkPlacementsService(session).add_debt(w['accounts']['t1'][0].id,w['homeworks'][0].id,nxt['id'])
    a,b=await asyncio.wait_for(asyncio.gather(run(),run()),timeout=20)
    assert a.id==b.id
    assert len(await history(c,w))==2


@pytest.mark.asyncio
async def test_new_earlier_next_archived_and_cancelled_excluded(client_for_tests,world):
    c,w=client_for_tests,world
    await setup(c,w)
    cancelled=await lesson(c,w,1,status='cancelled')
    assert (await history(c,w))[0]['due_at'] is None
    later=await lesson(c,w,7)
    r=await c.patch(f"/lessons/{cancelled['id']}",headers=headers(w,'t1'),json={'status':'scheduled'})
    assert r.status_code==200 and (await history(c,w))[0]['due_lesson_id']==cancelled['id']
    await c.delete(f"/lessons/{cancelled['id']}",headers=headers(w,'t1'))
    assert (await history(c,w))[0]['due_lesson_id']==later['id']


@pytest.mark.asyncio
async def test_purge_cascades_debts_and_deadline_journal(client_for_tests,world,session_db):
    c,w=client_for_tests,world
    await setup(c,w); target=await lesson(c,w,3); await debt(c,w,target['id'])
    cid=w['courses'][0].id
    r=await c.post(f'/courses/{cid}/purge',headers=headers(w,'admin'),
                  json={'confirm_course_id':cid,'confirm_name':w['courses'][0].name})
    assert r.status_code==200,r.text
    assert await session_db.scalar(select(func.count()).select_from(HomeworkPlacement).where(
        HomeworkPlacement.homework_id==w['homeworks'][0].id))==0
    assert len(await history(c,w,index=1))==1


@pytest.mark.asyncio
async def test_gap_lesson_and_placement_never_reappear_as_effective_deadline(client_for_tests,world,session_db):
    from src.modules.course_lifecycle.models import EnrollmentGap
    c,w=client_for_tests,world
    await setup(c,w); hidden=await lesson(c,w,2); later=await lesson(c,w,5)
    # The gap was between grants; its lesson and placement must stay hidden on re-enrollment.
    grant=await session_db.scalar(select(LessonStudent).where(LessonStudent.lesson_id==hidden['id']))
    enrollment=await session_db.scalar(select(StudentCourse).where(StudentCourse.course_id==w['courses'][0].id))
    session_db.add(EnrollmentGap(enrollment_id=enrollment.id,
        started_at=grant.created_at-timedelta(microseconds=1),ended_at=grant.created_at+timedelta(microseconds=1)))
    await session_db.commit()
    r=await c.patch(f"/lessons/{later['id']}",headers=headers(w,'t1'),json={'title':'Recalculate after re-enrollment'})
    assert r.status_code==200,r.text
    p=(await history(c,w))[0]
    assert p['due_lesson_id']==later['id']


@pytest.mark.asyncio
async def test_restore_lesson_inside_archived_course_keeps_deadlines_readonly(client_for_tests,world):
    c,w=client_for_tests,world
    await setup(c,w); target=await lesson(c,w,3)
    await c.delete(f"/lessons/{target['id']}",headers=headers(w,'t1'))
    before=await history(c,w)
    r=await c.delete(f"/courses/{w['courses'][0].id}",headers=headers(w,'t1'))
    assert r.status_code==200,r.text
    r=await c.post(f"/lessons/{target['id']}/restore",headers=headers(w,'admin'))
    assert r.status_code==200,r.text
    assert await history(c,w)==before


@pytest.mark.asyncio
@pytest.mark.parametrize('kind',['enrollment','teacher'])
async def test_reactivated_access_recalculates_deadline_without_opening_gap_lessons(client_for_tests,world,session_db,kind):
    from src.modules.teacher_students.models import TeacherStudent
    c,w=client_for_tests,world
    await setup(c,w); old=await lesson(c,w,3); next_lesson=await lesson(c,w,7)
    if kind=='enrollment':
        r=await c.delete(f"/courses/{w['courses'][0].id}/students/{w['accounts']['s1'][0].id}",headers=headers(w,'t1'))
        assert r.status_code==204,r.text
    else:
        await session_db.execute(update(TeacherStudent).where(TeacherStudent.teacher_id==w['teachers'][0].id)
            .values(ended_at=datetime.now(UTC)))
        await session_db.commit()
    # Changes while inactive preserve the previously visible history snapshot.
    await session_db.execute(update(Lesson).where(Lesson.id==old['id']).values(status='cancelled'))
    await session_db.commit()
    assert (await history(c,w))[0]['due_lesson_id']==old['id']
    if kind=='enrollment':
        r=await c.post(f"/courses/{w['courses'][0].id}/students",headers=headers(w,'t1'),
                       json={'student_user_id':w['accounts']['s1'][0].id})
        assert r.status_code==201,r.text
    else:
        r=await c.post('/teacher_students',headers=headers(w,'admin'),
            json={'teacher_user_id':w['accounts']['t1'][0].id,'student_user_id':w['accounts']['s1'][0].id})
        assert r.status_code in (200,201),r.text
    assert (await history(c,w))[0]['due_lesson_id']==next_lesson['id']
