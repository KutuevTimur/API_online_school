"""D12: exact per-meeting snapshots, teacher isolation, durable Moscow weeks."""
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import select, update

from src.modules.lessons.models import Lesson
from src.modules.teacher_students.models import TeacherStudent
from tests.modules.auth.test_t06_permissions import world, auth
from tests.modules.lessons.test_t08b_regular import preview, confirm, request


def headers(w, actor='t1'):
    return auth(w['accounts'][actor][1])


def price_url(w):
    return f"/teacher-planning/students/{w['accounts']['s1'][0].id}/price"


async def price(c, w, value, previous=None, actor='t1'):
    return await c.put(price_url(w), headers=headers(w, actor), json={
        'lesson_price_kopecks': value, 'expected_price_kopecks': previous})


async def create(c, w, at='2029-01-01T12:00:00+03:00', duration=55):
    r = await c.post('/lessons', headers=headers(w), json={
        'course_id': w['courses'][0].id, 'student_user_id': w['accounts']['s1'][0].id,
        'title': 'Synthetic priced meeting', 'scheduled_at': at, 'duration_minutes': duration})
    assert r.status_code == 201, r.text
    return r.json()['id']


async def earnings(c, w, week='2029-01-01', actor='t1'):
    r = await c.get('/teacher-planning/weekly-earnings', params={'week': week}, headers=headers(w, actor))
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_price_scope_validation_conflict_and_no_profile_leak(client_for_tests, world):
    c, w = client_for_tests, world
    assert (await c.get(price_url(w), headers=headers(w))).json() == {'lesson_price_kopecks': None}
    assert (await price(c,w,80025)).status_code == 200
    assert (await price(c,w,90000)).status_code == 409
    assert (await c.get(price_url(w),headers=headers(w,'t2'))).json() == {'lesson_price_kopecks': None}
    for bad in [-1, True, 1.25, '800', 2147483648]:
        assert (await price(c,w,bad,80025)).status_code == 422
    for actor in ['s1','admin']:
        assert (await c.get(price_url(w),headers=headers(w,actor))).status_code == 403
        assert (await price(c,w,0,80025,actor)).status_code == 403
        assert (await c.get('/teacher-planning/weekly-earnings',params={'week':'2029-01-01'},headers=headers(w,actor))).status_code == 403
    sid=w['accounts']['s2'][0].id
    assert (await c.get(f'/teacher-planning/students/{sid}/price',headers=headers(w))).status_code == 403
    for path in [f"/users/{w['accounts']['s1'][0].id}", '/users/students', f"/lessons/{w['lessons'][0].id}"]:
        assert 'price_kopecks' not in (await c.get(path,headers=headers(w,'s1'))).text
    for week in ['2029-01-02','9999-12-27']:
        assert (await c.get('/teacher-planning/weekly-earnings',params={'week':week},headers=headers(w))).status_code == 422


@pytest.mark.asyncio
async def test_snapshot_new_only_duration_move_archive_and_exact_total(client_for_tests, world, session_db):
    c,w=client_for_tests,world
    assert (await price(c,w,80025)).status_code==200
    first=await create(c,w,duration=30)
    assert (await price(c,w,100010,80025)).status_code==200
    second=await create(c,w,'2029-01-02T12:00:00+03:00',90)
    for lid, expected in [(first,80025),(second,100010)]:
        assert await session_db.scalar(select(Lesson.lesson_price_kopecks).where(Lesson.id==lid))==expected
        r=await c.patch(f'/lessons/{lid}',headers=headers(w),json={'status':'completed'})
        assert r.status_code==200,r.text
    assert (await earnings(c,w))==dict(week='2029-01-01',total_kopecks=180035,lesson_count=2,completed_count=2,unpriced_count=0)
    r=await c.patch(f'/lessons/{first}',headers=headers(w),json={'scheduled_at':'2028-12-31T23:00:00+03:00'})
    assert r.status_code==200,r.text
    assert (await earnings(c,w))['total_kopecks']==100010
    assert (await earnings(c,w,'2028-12-25'))['total_kopecks']==80025
    # A priced archived lesson must affect neither money nor the weekly count.
    assert (await c.delete(f'/lessons/{second}',headers=headers(w))).status_code==200
    assert (await earnings(c,w))==dict(week='2029-01-01',total_kopecks=0,lesson_count=0,completed_count=0,unpriced_count=0)
    assert await session_db.scalar(select(Lesson.lesson_price_kopecks).where(Lesson.id==second))==100010
    # An unpriced archived completion must not mark the active total incomplete.
    await session_db.execute(update(Lesson).where(Lesson.id==second).values(lesson_price_kopecks=None))
    await session_db.commit()
    assert (await earnings(c,w))['unpriced_count']==0
    # Archiving the course also excludes its otherwise unarchived lessons.
    assert (await c.delete(f'/courses/{w["courses"][0].id}',headers=headers(w))).status_code==200
    assert (await earnings(c,w,'2028-12-25'))==dict(week='2028-12-25',total_kopecks=0,lesson_count=0,completed_count=0,unpriced_count=0)
    assert await session_db.scalar(select(Lesson.lesson_price_kopecks).where(Lesson.id==first))==80025
    assert (await earnings(c,w,actor='t2'))['total_kopecks']==0


@pytest.mark.asyncio
async def test_legacy_unknown_zero_status_and_moscow_boundaries(client_for_tests, world, session_db):
    c,w=client_for_tests,world
    start=datetime(2029,1,1,tzinfo=ZoneInfo('Europe/Moscow'))
    lid=w['lessons'][0].id
    for at, expected in [(start-timedelta(microseconds=1),0),(start,1),(start+timedelta(days=7)-timedelta(microseconds=1),1),(start+timedelta(days=7),0)]:
        await session_db.execute(update(Lesson).where(Lesson.id==lid).values(scheduled_at=at,status='completed'))
        await session_db.commit()
        got=await earnings(c,w)
        assert got['unpriced_count']==expected and got['lesson_count']==expected
    await session_db.execute(update(Lesson).where(Lesson.id==lid).values(scheduled_at=start,status='cancelled'))
    await session_db.commit()
    assert (await earnings(c,w))['lesson_count']==0
    assert (await price(c,w,0)).status_code==200
    free=await create(c,w)
    got=await earnings(c,w)
    assert got['lesson_count']==1 and got['completed_count']==0 and got['unpriced_count']==0
    assert (await c.patch(f'/lessons/{free}',headers=headers(w),json={'status':'completed'})).status_code==200
    got=await earnings(c,w)
    assert got['completed_count']==1 and got['unpriced_count']==0 and got['total_kopecks']==0
    # Elapsed scheduled rows use exactly the same effective status as the UI.
    await session_db.execute(update(Lesson).where(Lesson.id==lid).values(scheduled_at=start,status='scheduled'))
    await session_db.commit()
    # Future scheduled is not yet money; past scheduled is automatically completed.
    old=await create(c,w,'2020-01-06T12:00:00+03:00')
    got=await earnings(c,w,'2020-01-06')
    assert got['completed_count']==1 and got['total_kopecks']==0 and got['unpriced_count']==0
    assert old


@pytest.mark.asyncio
async def test_regular_confirm_extend_snapshot_and_receipt(client_for_tests, world, session_db):
    c,w=client_for_tests,world
    p=await preview(c,w,request(w))
    assert (await price(c,w,80001)).status_code==200
    r=await confirm(c,w,p);assert r.status_code==200,r.text
    ids=r.json()['result']['lesson_ids']
    assert (await price(c,w,90002,80001)).status_code==200
    assert (await confirm(c,w,p)).json()==r.json()
    from uuid import uuid4
    extension=await preview(c,w,dict(operation_id=str(uuid4()),action='extend',series_id=r.json()['result']['series_id'],weeks=1))
    extended=await confirm(c,w,extension);assert extended.status_code==200,extended.text
    rows=(await session_db.execute(select(Lesson.id,Lesson.lesson_price_kopecks).where(Lesson.id.in_(ids+extended.json()['result']['lesson_ids'])))).all()
    assert dict(rows)=={**dict.fromkeys(ids,80001),**dict.fromkeys(extended.json()['result']['lesson_ids'],90002)}


@pytest.mark.asyncio
async def test_two_price_writes_conflict(world, not_open_session_db):
    from src.modules.teacher_planning.service import TeacherPlanningService
    from src.modules.teacher_planning.repository import TeacherPlanningRepository
    from src.modules.teacher_planning.models_dto import UpdateLessonPriceDTO
    from src.modules.base.exception import StaleUpdate
    async def save(value):
        async with not_open_session_db() as db:
            try:
                return await TeacherPlanningService(TeacherPlanningRepository(db)).price(world['accounts']['t1'][0],world['accounts']['s1'][0].id,UpdateLessonPriceDTO(lesson_price_kopecks=value,expected_price_kopecks=None))
            except StaleUpdate:return 409
    results=await asyncio.gather(save(1),save(2))
    assert results.count(409)==1


@pytest.mark.asyncio
async def test_registration_price_atomic_and_teacher_only(client_for_tests, world, session_db):
    c,w=client_for_tests,world
    data=dict(role='student',username='synthetic_price_new',first_name='Synthetic',last_name='Price',lesson_price_kopecks=80025)
    r=await c.post('/auth/register',headers=headers(w),json=data)
    assert r.status_code==200
    from src.modules.students.models import Student
    from src.modules.users.models import User
    value=await session_db.scalar(select(TeacherStudent.lesson_price_kopecks).join(Student).join(User,User.id==Student.user_id).where(User.username==data['username'],TeacherStudent.teacher_id==w['teachers'][0].id))
    assert value==80025
    assert (await c.post('/auth/register',headers=headers(w,'admin'),json={**data,'username':'synthetic_admin_price'})).status_code==403
