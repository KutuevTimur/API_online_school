"""T08: atomic recipient creation, scheduling semantics, meeting URLs and warnings."""
from datetime import datetime, UTC, timedelta

import pytest
from sqlalchemy import select, func, update

from src.modules.lessons.models import Lesson
from src.modules.lesson_students.models import LessonStudent
from src.modules.lesson_students.repository import LessonStudentsRepository
from src.modules.student_courses.models import StudentCourse
from src.modules.teacher_students.models import TeacherStudent
from src.modules.users.models import User
from tests.modules.auth.test_t06_permissions import world, auth


def body(w, **values):
    return {'course_id': w['courses'][0].id, 'title': 'Personal lesson',
            'scheduled_at': '2028-01-10T15:00:00+03:00', **values}


async def create(client, w, **values):
    return await client.post('/lessons', headers=auth(w['accounts']['t1'][1]), json=body(w, **values))


@pytest.mark.asyncio
async def test_auto_recipient_default_duration_utc_and_student_visibility(client_for_tests, world, session_db):
    w = world
    r = await create(client_for_tests, w)
    assert r.status_code == 201, r.text
    result = r.json()
    assert result['duration_minutes'] == 55 and result['status'] == 'scheduled'
    assert datetime.fromisoformat(result['scheduled_at']) == datetime(2028, 1, 10, 12, tzinfo=UTC)
    assert result['scheduled_at'].endswith('Z')
    assert 'teacher_id' not in result and 'student_id' not in result
    rows = (await session_db.execute(select(LessonStudent).where(LessonStudent.lesson_id == result['id']))).scalars().all()
    assert len(rows) == 1 and rows[0].student_id == w['students'][0].id
    for route in (f"/lessons/{result['id']}", '/lessons'):
        r = await client_for_tests.get(route, headers=auth(w['accounts']['s1'][1]))
        assert r.status_code == 200, r.text
        if route == '/lessons':
            assert result['id'] in [item['id'] for item in r.json()['items']]
    r = await client_for_tests.get('/lessons', headers=auth(w['accounts']['t1'][1]),
                                   params={'from_date': '2028-01-10T14:59:00+03:00', 'to_date': '2028-01-10T15:01:00+03:00'})
    assert [item['id'] for item in r.json()['items']] == [result['id']]


@pytest.mark.asyncio
@pytest.mark.parametrize('condition', ['none', 'expired', 'ended_link', 'disabled', 'history_revoked'])
async def test_no_active_recipient_never_creates_lesson(client_for_tests, world, session_db, condition):
    w = world
    if condition == 'none':
        await session_db.execute(update(StudentCourse).where(StudentCourse.course_id == w['courses'][0].id).values(is_deleted=True))
    elif condition == 'expired':
        await session_db.execute(update(StudentCourse).where(StudentCourse.course_id == w['courses'][0].id).values(expires_at=datetime.now(UTC)-timedelta(seconds=1)))
    elif condition == 'ended_link':
        await session_db.execute(update(TeacherStudent).where(TeacherStudent.teacher_id == w['teachers'][0].id).values(ended_at=datetime.now(UTC)))
    elif condition == 'disabled':
        await session_db.execute(update(User).where(User.id == w['accounts']['s1'][0].id).values(is_active=False))
    else:
        await session_db.execute(update(StudentCourse).where(StudentCourse.course_id == w['courses'][0].id).values(history_revoked=True))
    await session_db.commit()
    before = await session_db.scalar(select(func.count()).select_from(Lesson))
    r = await create(client_for_tests, w)
    assert r.status_code == 422, r.text
    assert await session_db.scalar(select(func.count()).select_from(Lesson)) == before


@pytest.mark.asyncio
async def test_multiple_students_need_explicit_public_id(client_for_tests, world, session_db):
    w = world
    # An explicit foreign/unlinked ID cannot silently fall back to the sole student.
    r = await create(client_for_tests, w, student_user_id=w['accounts']['s2'][0].id)
    assert r.status_code == 422
    session_db.add(StudentCourse(course_id=w['courses'][0].id, student_id=w['students'][1].id))
    session_db.add(TeacherStudent(teacher_id=w['teachers'][0].id, student_id=w['students'][1].id))
    await session_db.commit()
    assert (await create(client_for_tests, w)).status_code == 422
    r = await create(client_for_tests, w, student_user_id=w['accounts']['s2'][0].id)
    assert r.status_code == 201, r.text
    rows = list((await session_db.scalars(select(LessonStudent).where(LessonStudent.lesson_id == r.json()['id']))).all())
    assert len(rows) == 1 and rows[0].student_id == w['students'][1].id
    assert (await client_for_tests.get(f"/lessons/{r.json()['id']}", headers=auth(w['accounts']['s1'][1]))).status_code == 404


@pytest.mark.asyncio
async def test_failure_after_lesson_flush_rolls_back_entire_pair(client_for_tests, world, session_db, monkeypatch):
    before = [await session_db.scalar(select(func.count()).select_from(model)) for model in (Lesson, LessonStudent)]

    async def fail(self, data):
        raise RuntimeError('synthetic participant insert failure')

    monkeypatch.setattr(LessonStudentsRepository, 'add_student_to_lesson', fail)
    with pytest.raises(RuntimeError, match='synthetic participant'):
        await create(client_for_tests, world)
    after = [await session_db.scalar(select(func.count()).select_from(model)) for model in (Lesson, LessonStudent)]
    assert after == before


@pytest.mark.asyncio
@pytest.mark.parametrize('actor,status', [('s1',403), ('admin',403), ('t2',404)])
async def test_schedule_mutations_require_owning_teacher(client_for_tests, world, actor, status):
    headers = auth(world['accounts'][actor][1])
    # Role dependency rejects student/admin; invisible teacher objects are hidden.
    r = await client_for_tests.post('/lessons', headers=headers, json=body(world))
    assert r.status_code == status, r.text
    r = await client_for_tests.patch(f"/lessons/{world['lessons'][0].id}", headers=headers, json={'status': 'cancelled'})
    assert r.status_code == status, r.text


@pytest.mark.asyncio
async def test_move_cancel_complete_preserves_materials_and_archive_readonly(client_for_tests, world):
    w = world
    lid = w['lessons'][0].id
    headers = auth(w['accounts']['t1'][1])
    for values in ({'scheduled_at': '2028-01-12T18:00:00+03:00'}, {'status': 'cancelled'}, {'status': 'completed'}):
        r = await client_for_tests.patch(f'/lessons/{lid}', headers=headers, json=values)
        assert r.status_code == 200 and not r.json()['is_deleted'], r.text
        if 'status' in values:
            assert r.json()['status'] == values['status']
        else:
            assert r.json()['scheduled_at'] == '2028-01-12T15:00:00Z'
        for endpoint in (f'/lessons/{lid}', f'/lectures/{w["lectures"][0].id}/file?lesson_id={lid}&student_user_id={w["accounts"]["s1"][0].id}'):
            assert (await client_for_tests.get(endpoint, headers=auth(w['accounts']['s1'][1]))).status_code == 200
    r = await client_for_tests.get('/lessons', headers=headers, params={'status':'completed'})
    assert [item['id'] for item in r.json()['items']] == [lid] and r.json()['total'] == 1
    assert (await client_for_tests.delete(f'/lessons/{lid}', headers=headers)).status_code == 200
    assert (await client_for_tests.patch(f'/lessons/{lid}', headers=headers, json={'status':'scheduled'})).status_code == 403
    assert (await create(client_for_tests, w, course_id=w['courses'][1].id)).status_code == 404
    await client_for_tests.delete(f"/courses/{w['courses'][0].id}", headers=headers)
    assert (await create(client_for_tests, w)).status_code == 403


@pytest.mark.asyncio
async def test_conflict_intervals_self_cancelled_archived_course_and_other_teacher(client_for_tests, world):
    w = world
    headers = auth(w['accounts']['t1'][1])
    lid = w['lessons'][0].id
    r = await client_for_tests.patch(f'/lessons/{lid}', headers=headers,
                                    json={'scheduled_at':'2028-01-10T12:00:00Z','duration_minutes':55})
    assert r.status_code == 200 and not r.json()['warnings']
    r = await create(client_for_tests, w, scheduled_at='2028-01-10T12:55:00Z')
    assert r.status_code == 201 and not r.json()['warnings']
    new_id = r.json()['id']
    r = await client_for_tests.patch(f'/lessons/{new_id}', headers=headers, json={'scheduled_at':'2028-01-10T12:54:00Z'})
    assert r.status_code == 200 and r.json()['warnings'] == [{'code':'teacher_time_overlap','lesson_ids':[lid]}]
    # Neither detail nor student lists leak another pupil's conflict IDs.
    assert (await client_for_tests.get(f'/lessons/{new_id}', headers=auth(w['accounts']['s1'][1]))).json()['warnings'] == []
    r = await client_for_tests.patch(f'/lessons/{new_id}', headers=headers, json={'status':'cancelled'})
    assert r.status_code == 200 and r.json()['warnings'] == []
    await client_for_tests.patch(f'/lessons/{lid}', headers=headers, json={'status':'cancelled'})
    await client_for_tests.patch(f"/lessons/{w['lessons'][1].id}", headers=auth(w['accounts']['t2'][1]),
                                json={'scheduled_at':'2028-01-10T12:00:00Z'})
    r = await create(client_for_tests, w)
    assert r.status_code == 201 and not r.json()['warnings']
    # An archived course cannot produce a warning for another active course of its teacher.
    await client_for_tests.delete(f"/courses/{w['courses'][0].id}", headers=headers)
    course = await client_for_tests.post('/courses', headers=headers, json={'name':'Other active course','slug':'other-active'})
    assert course.status_code == 201, course.text
    cid = course.json()['id']
    enrolled = await client_for_tests.post(f'/courses/{cid}/students', headers=headers,
                                          json={'student_user_id':w['accounts']['s1'][0].id})
    assert enrolled.status_code == 201, enrolled.text
    r = await create(client_for_tests, w, course_id=cid)
    assert r.status_code == 201 and not r.json()['warnings']
    # The second teacher's concurrent interval is independently visible to them only.
    r = await client_for_tests.patch(f"/lessons/{w['lessons'][1].id}", headers=auth(w['accounts']['t2'][1]), json={'duration_minutes':60})
    assert r.status_code == 200 and not r.json()['warnings']


@pytest.mark.asyncio
async def test_url_fallback_override_clear_and_course_changes(client_for_tests, world):
    w = world
    headers = auth(w['accounts']['t1'][1])
    cid = w['courses'][0].id
    assert (await client_for_tests.patch(f'/courses/{cid}', headers=headers, json={'call_url':'https://example.com/room'})).status_code == 200
    r = await create(client_for_tests, w)
    assert r.status_code == 201 and r.json()['effective_call_url'] == 'https://example.com/room'
    lid = r.json()['id']
    r = await client_for_tests.patch(f'/lessons/{lid}', headers=headers, json={'call_url_override':'http://example.com/one-off'})
    assert r.status_code == 200 and r.json()['effective_call_url'] == 'http://example.com/one-off'
    await client_for_tests.patch(f'/courses/{cid}', headers=headers, json={'call_url':'https://example.com/new'})
    r = await client_for_tests.get(f'/lessons/{lid}', headers=auth(w['accounts']['s1'][1]))
    assert r.json()['effective_call_url'] == 'http://example.com/one-off'
    r = await client_for_tests.patch(f'/lessons/{lid}', headers=headers, json={'call_url_override':None})
    assert r.json()['effective_call_url'] == 'https://example.com/new'
    await client_for_tests.patch(f'/courses/{cid}', headers=headers, json={'call_url':None})
    r = await client_for_tests.get('/lessons', headers=headers)
    assert all(item['effective_call_url'] is None for item in r.json()['items'])


@pytest.mark.asyncio
@pytest.mark.parametrize('url', ['javascript:alert(1)', 'data:text/html,hi', 'file:///tmp/x', 'ftp://example.com/x', '//example.com/x', 'not a url'])
async def test_only_http_https_links(client_for_tests, world, url):
    headers = auth(world['accounts']['t1'][1])
    assert (await client_for_tests.patch(f"/courses/{world['courses'][0].id}", headers=headers, json={'call_url':url})).status_code == 422
    assert (await create(client_for_tests, world, call_url_override=url)).status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize('values', [{'scheduled_at':'2028-01-10T12:00:00'}, {'duration_minutes':None},
    {'duration_minutes':0}, {'duration_minutes':-1}, {'duration_minutes':True}, {'duration_minutes':1.5},
    {'status':'invalid'}, {'status':None}, {'title':None},
    {'scheduled_at':'9999-12-31T23:59:59Z'}, {'scheduled_at':'9999-12-31T23:59:59-03:00'}])
async def test_invalid_inputs_rejected_without_partial_data(client_for_tests, world, values):
    r = await create(client_for_tests, world, **values)
    assert r.status_code == 422, r.text
    r = await client_for_tests.patch(f"/lessons/{world['lessons'][0].id}",
        headers=auth(world['accounts']['t1'][1]), json=values)
    assert r.status_code == 422, r.text


@pytest.mark.asyncio
async def test_duration_change_and_completed_intervals_warn(client_for_tests, world):
    w = world
    headers = auth(w['accounts']['t1'][1])
    lid = w['lessons'][0].id
    await client_for_tests.patch(f'/lessons/{lid}', headers=headers,
        json={'scheduled_at':'2028-01-10T12:00:00Z','duration_minutes':55,'status':'completed'})
    r = await create(client_for_tests, w, scheduled_at='2028-01-10T12:55:00Z')
    assert r.status_code == 201 and not r.json()['warnings']
    new_id = r.json()['id']
    r = await client_for_tests.patch(f'/lessons/{lid}', headers=headers, json={'duration_minutes':56})
    assert r.status_code == 200 and r.json()['warnings'] == [{'code':'teacher_time_overlap','lesson_ids':[new_id]}]
    await client_for_tests.delete(f'/lessons/{new_id}', headers=headers)
    r = await client_for_tests.patch(f'/lessons/{lid}', headers=headers, json={'duration_minutes':57})
    assert r.status_code == 200 and not r.json()['warnings']


@pytest.mark.asyncio
async def test_failure_after_pair_insert_rolls_back(client_for_tests, world, session_db, monkeypatch):
    from src.modules.lessons.repository import LessonsRepository
    before = [await session_db.scalar(select(func.count()).select_from(model)) for model in (Lesson, LessonStudent)]

    async def fail(self, *args):
        raise RuntimeError('synthetic warning query failure')

    monkeypatch.setattr(LessonsRepository, 'overlapping_ids', fail)
    with pytest.raises(RuntimeError, match='warning query'):
        await create(client_for_tests, world)
    assert [await session_db.scalar(select(func.count()).select_from(model)) for model in (Lesson, LessonStudent)] == before


@pytest.mark.asyncio
async def test_concurrent_creates_preserve_pairs_and_warn(config_fix, world):
    import asyncio
    from src.modules.lessons.depends import get_lessons_service
    from src.modules.lessons.models_dto import CreateLessonRequestDTO

    async def run():
        async with config_fix.db_connection.session_local() as session:
            service = get_lessons_service(session=session)
            return await service.create_lesson(world['accounts']['t1'][0].id,
                                              CreateLessonRequestDTO(**body(world)))

    first, second = await asyncio.wait_for(asyncio.gather(run(), run()), timeout=20)
    assert first.id != second.id
    assert sorted(bool(result.warnings) for result in (first, second)) == [False, True]
    async with config_fix.db_connection.session_local() as session:
        for result in (first, second):
            rows = list((await session.scalars(select(LessonStudent).where(LessonStudent.lesson_id == result.id))).all())
            assert len(rows) == 1 and rows[0].student_id == world['students'][0].id
