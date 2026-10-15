"""T10 acceptance on guarded PostgreSQL, including independent-session races."""
import asyncio
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, update

from src.modules.homework_submissions.depends import get_homework_submissions_service
from src.modules.homework_submissions.exception import SubmissionConflict, HomeworkSubmissionNotEditable
from src.modules.homework_submissions.models import HomeworkSubmission, HomeworkSubmissionStatus as Status
from src.modules.homework_submissions.models_dto import UpdateSubmissionTeacherRequestDTO, UpdateSubmissionStudentRequestDTO
from src.modules.courses.models import Course
from src.modules.lessons.models import Lesson
from src.modules.lesson_students.models import LessonStudent
from src.modules.student_courses.models import StudentCourse
from src.modules.teacher_students.models import TeacherStudent
from tests.modules.auth.test_t06_permissions import world
from tests.modules.homework_submissions.test_t09_lifecycle import route, headers


async def submit(client, w, index=0):
    r = await client.post(route(w, '/submit', index), headers=headers(w))
    assert r.status_code == 200, r.text
    return r.json()['version']


@pytest.mark.asyncio
@pytest.mark.parametrize('grade', [0, 5])
async def test_review_result_and_immutable(client_for_tests, world, session_db, grade):
    w = world
    version = await submit(client_for_tests, w)
    r = await client_for_tests.patch(route(w, '/teacher'), headers=headers(w, 't1'),
        json={'grade': grade, 'expected_version': version})
    assert r.status_code == 200, r.text
    result = r.json()
    assert result['grade'] == grade and result['teacher_comment'] is None
    assert result['status'] == 'checked' and result['version'] == version + 1
    assert result['checked_by'] == w['accounts']['t1'][0].id
    assert result['checked_at'].endswith('Z')
    assert result['submitted_at'] is not None
    stored = await session_db.scalar(select(HomeworkSubmission).where(HomeworkSubmission.id == result['id']))
    assert stored.checked_by == w['teachers'][0].id and stored.version == version + 1
    r = await client_for_tests.get(route(w), headers=headers(w))
    assert r.json() == result
    r = await client_for_tests.get(f"/homeworks/{w['homeworks'][0].id}/submissions", headers=headers(w))
    assert r.json()['items'][0] == result
    r = await client_for_tests.patch(route(w, '/teacher'), headers=headers(w, 't1'),
        json={'grade': 1, 'expected_version': version + 1, 'teacher_comment': 'change'})
    assert r.status_code == 403
    r = await client_for_tests.get('/submissions/review-queue', headers=headers(w, 't1'))
    assert r.json()['total'] == 0


@pytest.mark.asyncio
@pytest.mark.parametrize('payload', [
    {}, {'grade': 1}, {'expected_version': 2},
    *[{'grade': x, 'expected_version': 2} for x in [-1, 6, 2.5, 5.0, True, '5', None]],
    *[{'grade': 1, 'expected_version': x} for x in [0, -1, True, '2', None]],
    {'grade': 1, 'expected_version': 2, 'status': 'draft'},
    {'grade': 1, 'expected_version': 2, 'checked_by': 999},
])
async def test_review_validation(client_for_tests, world, payload):
    w = world
    await submit(client_for_tests, w)
    r = await client_for_tests.patch(route(w, '/teacher'), headers=headers(w, 't1'), json=payload)
    assert r.status_code == 422, r.text
    r = await client_for_tests.get(route(w), headers=headers(w))
    assert r.json()['status'] == 'submitted' and r.json()['version'] == 2


@pytest.mark.asyncio
async def test_draft_stale_and_object_boundaries(client_for_tests, world):
    w = world
    payload = {'grade': 3, 'expected_version': 1}
    r = await client_for_tests.patch(route(w, '/teacher'), headers=headers(w, 't1'), json=payload)
    assert r.status_code == 409
    version = await submit(client_for_tests, w)
    payload['expected_version'] = version
    for actor, code in [('t2', 404), ('s1', 403), ('admin', 403)]:
        r = await client_for_tests.patch(route(w, '/teacher'), headers=headers(w, actor), json=payload)
        assert r.status_code == code, r.text
    r = await client_for_tests.patch(route(w, '/student'), headers=headers(w), data={'text_content': 'new version'})
    assert r.json()['version'] == version + 1
    r = await client_for_tests.patch(route(w, '/teacher'), headers=headers(w, 't1'), json=payload)
    assert r.status_code == 409
    payload.update(expected_version=version + 1, teacher_comment='Reviewed current answer')
    r = await client_for_tests.patch(route(w, '/teacher'), headers=headers(w, 't1'), json=payload)
    assert r.status_code == 200 and r.json()['teacher_comment'] == payload['teacher_comment']


@pytest.mark.asyncio
async def test_queue_scopes_filters_pagination_current_version(client_for_tests, world):
    w = world
    # Drafts are not queued.
    assert (await client_for_tests.get('/submissions/review-queue', headers=headers(w, 't1'))).json()['total'] == 0
    for i in [0, 1]:
        await submit(client_for_tests, w, i)
    await client_for_tests.patch(route(w, '/student'), headers=headers(w), data={'text_content': 'latest'})
    for i, actor in enumerate(['t1', 't2']):
        r = await client_for_tests.get('/submissions/review-queue', headers=headers(w, actor))
        assert r.status_code == 200, r.text
        body = r.json(); assert body['total'] == 1
        item = body['items'][0]
        assert item['id'] == w['submissions'][i].id and item['course_id'] == w['courses'][i].id
        assert item['lesson_id'] == w['lessons'][i].id and item['student_user_id'] == w['accounts']['s1'][0].id
        assert item['version'] == (3 if i == 0 else 2)
        assert 'file_path' not in str(item) and 'student_id' not in item and 'teacher_id' not in item
        for filters, total in [({'offset': 99}, 1), ({'course_id': w['courses'][1-i].id}, 0),
            ({'student_user_id': w['accounts']['s2'][0].id}, 0),
            ({'course_id': w['courses'][i].id, 'student_user_id': w['accounts']['s1'][0].id}, 1)]:
            r = await client_for_tests.get('/submissions/review-queue', headers=headers(w, actor), params=filters)
            assert r.status_code == 200 and r.json()['total'] == total, r.text
            if filters.get('offset') or not total:
                assert r.json()['items'] == []
    for actor in ['s1', 'admin']:
        assert (await client_for_tests.get('/submissions/review-queue', headers=headers(w, actor))).status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize('condition', ['course', 'lesson', 'expired', 'unlink', 'recipient', 'teacher', 'history'])
async def test_queue_excludes_readonly_and_history(client_for_tests, world, session_db, condition):
    w = world
    await submit(client_for_tests, w)
    if condition == 'course': stmt = update(Course).where(Course.id == w['courses'][0].id).values(is_deleted=True)
    elif condition == 'lesson': stmt = update(Lesson).where(Lesson.id == w['lessons'][0].id).values(is_deleted=True)
    elif condition == 'expired': stmt = update(StudentCourse).where(StudentCourse.course_id == w['courses'][0].id).values(expires_at=datetime.now(UTC)-timedelta(seconds=1))
    elif condition == 'unlink': stmt = update(StudentCourse).where(StudentCourse.course_id == w['courses'][0].id).values(access_ended_at=datetime.now(UTC))
    elif condition == 'recipient': stmt = update(LessonStudent).where(LessonStudent.id == w['recipients'][0].id).values(access_ended_at=datetime.now(UTC))
    elif condition == 'teacher': stmt = update(TeacherStudent).where(TeacherStudent.teacher_id == w['teachers'][0].id).values(ended_at=datetime.now(UTC))
    else: stmt = update(HomeworkSubmission).where(HomeworkSubmission.id == w['submissions'][0].id).values(is_working=False)
    await session_db.execute(stmt); await session_db.commit()
    r = await client_for_tests.get('/submissions/review-queue', headers=headers(w, 't1'))
    assert r.status_code == 200 and r.json()['total'] == 0, r.text
    r = await client_for_tests.patch(route(w, '/teacher'), headers=headers(w, 't1'), json={'grade': 4, 'expected_version': 2})
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
@pytest.mark.parametrize('competitor', ['edit', 'check'])
async def test_concurrent_review_serializes(config_fix, client_for_tests, world, competitor):
    w = world; version = await submit(client_for_tests, w)
    hid, sid = w['homeworks'][0].id, w['submissions'][0].id
    async def run(action):
        async with config_fix.db_connection.session_local() as session:
            service = get_homework_submissions_service(session=session, config=config_fix)
            try:
                if action == 'edit':
                    return await service.update_submission_student(w['accounts']['s1'][0].id, hid, sid,
                        UpdateSubmissionStudentRequestDTO(text_content='racing edit'))
                return await service.update_submission_teacher(w['accounts']['t1'][0].id, hid, sid,
                    UpdateSubmissionTeacherRequestDTO(expected_version=version, grade=4))
            except (SubmissionConflict, HomeworkSubmissionNotEditable) as exc:
                return type(exc).__name__
    results = await asyncio.wait_for(asyncio.gather(run('check'), run(competitor)), timeout=15)
    assert sum(isinstance(x, str) for x in results) == 1, results
    r = await client_for_tests.get(route(w), headers=headers(w))
    final = r.json(); assert final['version'] == version + 1
    if final['status'] == 'checked':
        assert final['text_content'] == 'Submission text' and final['grade'] == 4
    else:
        assert competitor == 'edit' and final['text_content'] == 'racing edit' and final['grade'] is None


@pytest.mark.asyncio
async def test_review_commit_failure_rolls_back(client_for_tests, world, monkeypatch):
    from sqlalchemy.ext.asyncio import AsyncSession
    w = world; version = await submit(client_for_tests, w)
    async def fail(*args, **kwargs):
        raise RuntimeError('synthetic review commit failure')
    monkeypatch.setattr(AsyncSession, 'commit', fail)
    with pytest.raises(RuntimeError, match='review commit'):
        await client_for_tests.patch(route(w, '/teacher'), headers=headers(w, 't1'),
            json={'grade': 3, 'expected_version': version})
    monkeypatch.undo()
    r = await client_for_tests.get(route(w), headers=headers(w))
    data = r.json()
    assert data['version'] == version and data['status'] == 'submitted'
    assert data['checked_at'] is None and data['checked_by'] is None and data['grade'] is None
    assert (await client_for_tests.get('/submissions/review-queue', headers=headers(w, 't1'))).json()['total'] == 1


@pytest.mark.asyncio
async def test_queue_order_page_and_history_filter(client_for_tests, world, session_db,
    create_homework_fixture, create_homework_submission_fixture):
    from tests.modules.homeworks.fixtures.models_dto import CreateHomeworkFixtureDTO
    from tests.modules.homework_submissions.fixtures.models_dto import CreateHomeworkSubmissionFixtureDTO
    w = world
    await submit(client_for_tests, w)
    same_time = datetime.now(UTC)-timedelta(days=1)
    ids = []
    for is_working, status in [(True, Status.SUBMITTED), (True, Status.SUBMITTED),
                               (False, Status.SUBMITTED), (True, Status.CHECKED)]:
        hw = await create_homework_fixture(CreateHomeworkFixtureDTO(lesson_student_id=w['recipients'][0].id))
        sub = await create_homework_submission_fixture(CreateHomeworkSubmissionFixtureDTO(homework_id=hw.id,
            status=status))
        await session_db.execute(update(HomeworkSubmission).where(HomeworkSubmission.id == sub.id).values(is_working=is_working, submitted_at=same_time))
        await session_db.commit()
        if is_working and status == Status.SUBMITTED:
            ids.append(sub.id)
    for offset, expected in [(0, ids[0]), (1, ids[1]), (2, w['submissions'][0].id), (3, None)]:
        r = await client_for_tests.get('/submissions/review-queue', headers=headers(w, 't1'), params={'limit': 1, 'offset': offset})
        assert r.status_code == 200 and r.json()['total'] == 3, r.text
        assert [x['id'] for x in r.json()['items']] == ([expected] if expected else [])


@pytest.mark.asyncio
async def test_queue_missing_teacher_profile_fails_closed(client_for_tests, world, session_db):
    from src.modules.users.models import User, UserRole
    w = world
    # A role change does not manufacture a teacher profile or an unscoped queue.
    await session_db.execute(update(User).where(User.id == w['accounts']['s2'][0].id).values(role=UserRole.TEACHER))
    await session_db.commit()
    r = await client_for_tests.get('/submissions/review-queue', headers=headers(w, 's2'))
    assert r.status_code == 200 and r.json()['items'] == [] and r.json()['total'] == 0
