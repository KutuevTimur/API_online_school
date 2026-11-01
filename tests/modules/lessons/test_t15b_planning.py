from datetime import datetime, UTC, timedelta
from zoneinfo import ZoneInfo
import pytest
from sqlalchemy import update, delete, select
from src.modules.lessons.models import Lesson
from src.modules.lectures.models import Lecture
from src.modules.homeworks.models import Homework
from src.modules.teacher_students.models import TeacherStudent
from src.modules.lesson_students.models import LessonStudent
from tests.modules.auth.test_t06_permissions import world, auth


def monday():
    now = datetime.now(ZoneInfo('Europe/Moscow')).date()
    return now - timedelta(days=now.weekday())


@pytest.mark.asyncio
async def test_norm_history_exception_revision_and_scope(client_for_tests, world):
    c=client_for_tests; w=world; h=auth(w['accounts']['t1'][1]); sid=w['accounts']['s1'][0].id
    url=f'/teacher-planning/students/{sid}/norm'; week=monday(); following=week+timedelta(days=7)
    async def read(when, actor='t1'):
        r=await c.get('/teacher-planning/students',params={'week':str(when)},headers=auth(w['accounts'][actor][1]))
        assert r.status_code==200,r.text
        return r.json()['items'][0]
    assert (await read(week))['target'] is None
    data=dict(week=str(following),target=2,expected_revision=0)
    assert (await c.put(url,headers=h,json=data)).status_code==200
    assert (await c.put(url,headers=h,json=data)).status_code==409
    assert (await read(week))['target'] is None
    assert (await read(following))['target']==2
    assert (await read(following,'t2'))['target'] is None
    assert (await c.put(url,headers=h,json=dict(week=str(week),target=1,expected_revision=1))).status_code==422
    assert (await c.put(url,headers=h,json=dict(week=str(week),kind='exception',target=1,paused=True,expected_revision=1))).status_code==200
    assert (await read(week))['paused'] is True
    assert (await read(following))['target']==2 and not (await read(following))['paused']
    assert (await c.put(url,headers=h,json=dict(week=str(week-timedelta(days=7)),kind='exception',target=3,expected_revision=2))).status_code==422
    assert (await c.put(url,headers=auth(w['accounts']['s1'][1]),json=data)).status_code==403
    for invalid in [0, -1, True, 1.5]:
        assert (await c.put(url,headers=h,json={**data,'target':invalid})).status_code==422


@pytest.mark.asyncio
async def test_reminders_recipient_scope_waivers_filters_and_archive(client_for_tests, world, session_db):
    c=client_for_tests;w=world;h=auth(w['accounts']['t1'][1]);sid=w['accounts']['s1'][0].id;lid=w['lessons'][0].id
    await session_db.execute(delete(Lecture).where(Lecture.id==w['lectures'][0].id))
    await session_db.execute(update(Lesson).where(Lesson.id==lid).values(scheduled_at=datetime.now(UTC)-timedelta(days=1)))
    await session_db.commit()
    async def reminders(actor='t1', **params):
        r=await c.get('/teacher-planning/reminders',headers=auth(w['accounts'][actor][1]),params=params)
        assert r.status_code==200,r.text
        return r.json()
    row=(await reminders())['items'][0]
    assert row['needs_lecture'] and not row['needs_homework']
    assert not (await reminders('t2'))['items']
    students=await c.get('/users/students',headers=h,params={'attention':'lecture','sort':'attention','limit':1})
    assert students.status_code==200,students.text
    assert students.json()['total']==1 and students.json()['items'][0]['missing_lecture']==1
    assert (await c.get('/users/students',headers=h,params={'attention':'lecture','offset':1})).json()['total']==1
    url=f'/teacher-planning/lessons/{lid}/students/{sid}'
    assert (await c.patch(url,headers=auth(w['accounts']['t2'][1]),json={'lecture_not_needed':True})).status_code in (403,404)
    assert (await c.patch(url,headers=h,json={'lecture_not_needed':True})).status_code==200
    assert not (await reminders())['items']
    assert (await c.patch(url,headers=h,json={'lecture_not_needed':False})).status_code==200
    assert (await reminders())['total']==1
    await session_db.execute(update(Lesson).where(Lesson.id==lid).values(status='cancelled'));await session_db.commit()
    assert not (await reminders())['items']
    await session_db.execute(update(Lesson).where(Lesson.id==lid).values(status='scheduled',scheduled_at=datetime.now(UTC)+timedelta(days=1)));await session_db.commit()
    assert not (await reminders())['items']
    await session_db.execute(update(Lesson).where(Lesson.id==lid).values(status='completed'));await session_db.commit()
    assert (await reminders())['total']==1
    await c.delete(f'/courses/{w["courses"][0].id}',headers=h)
    assert not (await reminders())['items']


@pytest.mark.asyncio
async def test_week_count_moscow_bounds_all_courses_not_other_teacher(client_for_tests, world, session_db):
    w=world;c=client_for_tests; week=monday();start=datetime.combine(week,datetime.min.time(),ZoneInfo('Europe/Moscow'))
    lid=w['lessons'][0].id;h=auth(w['accounts']['t1'][1])
    async def count():
        r=await c.get('/teacher-planning/students',headers=h,params={'week':str(week)})
        assert r.status_code==200,r.text
        return r.json()['items'][0]['scheduled_count']
    for at, expected in [(start-timedelta(microseconds=1),0),(start,1),(start+timedelta(days=7)-timedelta(microseconds=1),1),(start+timedelta(days=7),0)]:
        await session_db.execute(update(Lesson).where(Lesson.id==lid).values(scheduled_at=at));await session_db.commit()
        assert await count()==expected
    await session_db.execute(update(Lesson).where(Lesson.id==lid).values(scheduled_at=start,status='cancelled'));await session_db.commit()
    assert await count()==0


@pytest.mark.asyncio
async def test_deficit_scope_before_paging_and_pause(client_for_tests,world):
    c=client_for_tests;w=world;week=monday();sid=w['accounts']['s1'][0].id;h=auth(w['accounts']['t1'][1])
    url=f'/teacher-planning/students/{sid}/norm'
    assert (await c.put(url,headers=h,json=dict(week=str(week),kind='exception',target=8,expected_revision=0))).status_code==200
    for offset, count in [(0,1),(1,0)]:
        r=await c.get('/teacher-planning/students',headers=h,params={'week':str(week),'deficit_only':True,'limit':1,'offset':offset})
        assert r.status_code==200,r.text
        assert r.json()['total']==1 and len(r.json()['items'])==count
    r=await c.get('/teacher-planning/students',headers=auth(w['accounts']['t2'][1]),params={'week':str(week),'deficit_only':True})
    assert r.json()['total']==0
    assert (await c.put(url,headers=h,json=dict(week=str(week),kind='exception',target=8,paused=True,expected_revision=1))).status_code==200
    r=await c.get('/teacher-planning/students',headers=h,params={'week':str(week),'deficit_only':True})
    assert r.json()['total']==0


@pytest.mark.asyncio
async def test_two_tab_norm_write_conflict_is_atomic(world,not_open_session_db):
    import asyncio
    from src.modules.teacher_planning.service import TeacherPlanningService
    from src.modules.teacher_planning.repository import TeacherPlanningRepository
    from src.modules.teacher_planning.models_dto import NormRequestDTO
    from src.modules.base.exception import StaleUpdate
    sid=world['accounts']['s1'][0].id;actor=world['accounts']['t1'][0]
    async def save(target):
        async with not_open_session_db() as db:
            try:
                return await TeacherPlanningService(TeacherPlanningRepository(db)).norm(actor,sid,
                    NormRequestDTO(week=monday(),kind='exception',target=target,expected_revision=0))
            except StaleUpdate:
                return 409
    results=await asyncio.gather(save(2),save(3))
    assert sum(isinstance(r,dict) for r in results)==1 and 409 in results


@pytest.mark.asyncio
async def test_reminder_enrollment_is_correlated_to_exact_recipient(client_for_tests,world,session_db):
    from src.modules.student_courses.models import StudentCourse
    w=world; c=client_for_tests;lid=w['lessons'][0].id;h=auth(w['accounts']['t1'][1])
    other=w['students'][1];own=w['students'][0];course=w['courses'][0]
    session_db.add(TeacherStudent(teacher_id=w['teachers'][0].id,student_id=other.id))
    session_db.add(StudentCourse(course_id=course.id,student_id=other.id))
    session_db.add(LessonStudent(lesson_id=lid,student_id=other.id))
    await session_db.execute(update(Lesson).where(Lesson.id==lid).values(status='completed'))
    await session_db.execute(delete(Lecture).where(Lecture.id==w['lectures'][0].id))
    await session_db.execute(update(StudentCourse).where(StudentCourse.course_id==course.id,StudentCourse.student_id==own.id).values(access_ended_at=datetime.now(UTC)))
    await session_db.commit()
    r=await c.get('/teacher-planning/reminders',headers=h)
    assert r.status_code==200,r.text
    assert r.json()['total']==1
    assert {row['student_user_id'] for row in r.json()['items']}=={other.user_id}
    assert r.json()['items'][0]['needs_homework'] and r.json()['items'][0]['needs_lecture']
