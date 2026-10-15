"""Synthetic T13 acceptance through real routes and guarded PostgreSQL."""
from datetime import datetime, UTC, timedelta
import asyncio
import pytest
from sqlalchemy import select, update, delete, func
from src.modules.notifications.models import Notification
from src.modules.notifications.repository import NotificationsRepository
from src.modules.notifications.service import NotificationsService
from src.modules.audit_events.service import AuditEventsService
from src.modules.account_invitations.models import AccountAudit
from src.modules.course_lifecycle.models import LifecycleAudit
from src.modules.homework_submissions.models import HomeworkSubmission, HomeworkSubmissionFile
from src.modules.homeworks.models import Homework
from src.modules.student_courses.models import StudentCourse
from src.modules.teacher_students.models import TeacherStudent
from src.modules.lessons.service import LessonsService
from tests.modules.auth.test_t06_permissions import world
from tests.modules.homework_submissions.test_t09_lifecycle import route, headers


async def inbox(client, w, actor='s1', **params):
    r = await client.get('/notifications', headers=headers(w, actor), params=params)
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_homework_creation_and_no_payload(client_for_tests, world):
    w = world
    r = await client_for_tests.post('/homeworks', headers=headers(w, 't1'), data={
        'lesson_id': w['lessons'][0].id, 'student_user_id': w['accounts']['s1'][0].id,
        'title': 'PRIVATE TITLE', 'description': 'PRIVATE DESCRIPTION'})
    assert r.status_code == 201, r.text
    body = await inbox(client_for_tests, w)
    assert body['total'] == 1
    n = body['items'][0]
    assert n['event_type'] == 'homework_assigned' and n['object_id'] == r.json()['id']
    assert 'PRIVATE' not in str(body) and 'recipient_user_id' not in n and 'dedupe_key' not in n
    target = await client_for_tests.get(f"/notifications/{n['id']}/target", headers=headers(w))
    assert target.json()['available'] is True and target.json()['object_type'] == 'homework'


@pytest.mark.asyncio
async def test_submit_edit_retry_review(client_for_tests, world):
    w = world
    r = await client_for_tests.post(route(w, '/submit'), headers=headers(w))
    assert r.status_code == 200, r.text
    first = await inbox(client_for_tests, w, 't1')
    assert first['total'] == 1 and first['items'][0]['event_type'] == 'solution_submitted'
    await client_for_tests.post(route(w, '/submit'), headers=headers(w))
    r = await client_for_tests.patch(route(w, '/student'), headers=headers(w), data={'text_content': 'PRIVATE ANSWER'})
    assert r.status_code == 200
    assert (await inbox(client_for_tests, w, 't1')) == first
    assert (await inbox(client_for_tests, w, 't2'))['total'] == 0
    target = await client_for_tests.get(f"/notifications/{first['items'][0]['id']}/target", headers=headers(w, 't1'))
    assert target.json()['available'] and target.json()['homework_id'] == w['homeworks'][0].id
    r = await client_for_tests.patch(route(w, '/teacher'), headers=headers(w, 't1'),
        json={'expected_version': r.json()['version'], 'grade': 5, 'teacher_comment': 'PRIVATE COMMENT'})
    assert r.status_code == 200, r.text
    student = await inbox(client_for_tests, w)
    assert student['total'] == 1 and student['items'][0]['event_type'] == 'solution_checked'
    assert 'PRIVATE' not in str(student)
    assert (await inbox(client_for_tests, w, 's2'))['total'] == 0


@pytest.mark.asyncio
async def test_lesson_real_transitions_only(client_for_tests, world):
    w = world
    url = f"/lessons/{w['lessons'][0].id}"
    data = {'scheduled_at': (datetime.now(UTC) + timedelta(days=4)).isoformat()}
    for _ in range(2):
        r = await client_for_tests.patch(url, headers=headers(w, 't1'), json=data)
        assert r.status_code == 200, r.text
    assert (await inbox(client_for_tests, w))['total'] == 1
    for _ in range(2):
        r = await client_for_tests.patch(url, headers=headers(w, 't1'), json={'status': 'cancelled'})
        assert r.status_code == 200, r.text
    rows = (await inbox(client_for_tests, w))['items']
    assert {n['event_type'] for n in rows} == {'lesson_rescheduled', 'lesson_cancelled'}
    assert len(rows) == 2
    assert (await inbox(client_for_tests, w, 's2'))['total'] == 0
    await client_for_tests.patch(url, headers=headers(w, 't1'), json={'status': 'scheduled'})
    await client_for_tests.patch(url, headers=headers(w, 't1'), json={'status': 'cancelled'})
    assert (await inbox(client_for_tests, w))['total'] == 3


@pytest.mark.asyncio
@pytest.mark.parametrize('actor', ['s2', 't2', 'admin'])
async def test_foreign_notification_is_hidden(client_for_tests, world, session_db, actor):
    w = world
    await NotificationsService(session_db).homework_event(w['homeworks'][0].id, 'homework_assigned')
    await session_db.commit()
    n = (await inbox(client_for_tests, w))['items'][0]
    assert (await inbox(client_for_tests, w, actor))['total'] == 0
    for method, suffix in [('get', 'target'), ('patch', 'read')]:
        r = await getattr(client_for_tests, method)(f"/notifications/{n['id']}/{suffix}", headers=headers(w, actor))
        assert r.status_code == 404, r.text


@pytest.mark.asyncio
async def test_read_idempotent_counts_pagination(client_for_tests, world, session_db):
    w = world; service = NotificationsService(session_db)
    for h in w['homeworks']:
        await service.homework_event(h.id, 'homework_assigned')
        await service.homework_event(h.id, 'homework_assigned')
    await session_db.commit()
    page = await inbox(client_for_tests, w, limit=1)
    assert page['total'] == 2 and len(page['items']) == 1
    assert (await inbox(client_for_tests, w, offset=99))['total'] == 2
    assert (await inbox(client_for_tests, w, offset=99))['items'] == []
    url = f"/notifications/{page['items'][0]['id']}/read"
    first = await client_for_tests.patch(url, headers=headers(w))
    second = await client_for_tests.patch(url, headers=headers(w))
    assert first.status_code == 200 and first.json()['read_at'] == second.json()['read_at']
    assert (await inbox(client_for_tests, w, unread_only=True))['total'] == 1
    assert (await client_for_tests.get('/notifications/unread', headers=headers(w))).json() == {'unread': 1}
    assert (await inbox(client_for_tests, w))['total'] == 2


@pytest.mark.asyncio
@pytest.mark.parametrize('revoke', ['history', 'purge', 'submission'])
async def test_target_rechecks_access(client_for_tests, world, session_db, revoke):
    w = world; h = w['homeworks'][0].id
    service = NotificationsService(session_db)
    await service.homework_event(h, 'solution_checked', w['submissions'][0].id) if revoke == 'submission' else await service.homework_event(h, 'homework_assigned')
    await session_db.commit()
    n = (await inbox(client_for_tests, w))['items'][0]
    if revoke == 'history':
        await session_db.execute(update(StudentCourse).where(StudentCourse.course_id == w['courses'][0].id).values(history_revoked=True))
    else:
        await session_db.execute(delete(HomeworkSubmissionFile).where(HomeworkSubmissionFile.submission_id == w['submissions'][0].id))
        await session_db.execute(delete(HomeworkSubmission).where(HomeworkSubmission.id == w['submissions'][0].id))
        if revoke == 'purge':
            await session_db.execute(delete(Homework).where(Homework.id == h))
    await session_db.commit()
    r = await client_for_tests.get(f"/notifications/{n['id']}/target", headers=headers(w))
    assert r.status_code == 200 and r.json()['available'] is False and r.json()['message']
    assert r.json()['object_id'] is None
    assert (await inbox(client_for_tests, w))['total'] == 1
    assert (await client_for_tests.patch(f"/notifications/{n['id']}/read", headers=headers(w))).status_code == 200


@pytest.mark.asyncio
async def test_rollback_after_staged_submission(client_for_tests, world, session_db, monkeypatch):
    original = NotificationsService.homework_event
    async def fail(self, *args, **kwargs):
        await original(self, *args, **kwargs)
        raise RuntimeError('injected after notification insert')
    monkeypatch.setattr(NotificationsService, 'homework_event', fail)
    with pytest.raises(RuntimeError, match='injected'):
        await client_for_tests.post(route(world, '/submit'), headers=headers(world))
    assert await session_db.scalar(select(func.count()).select_from(Notification)) == 0
    assert await session_db.scalar(select(HomeworkSubmission.status).where(HomeworkSubmission.id == world['submissions'][0].id)) == 'draft'


@pytest.mark.asyncio
async def test_dedupe_with_independent_sessions(world, config_fix, session_db):
    user = world['accounts']['s1'][0].id
    async def stage():
        async with config_fix.db_connection.session_local() as s:
            await NotificationsRepository(s).stage(user, 'homework_assigned', 'homework', world['homeworks'][0].id, 'same-event')
            await s.commit()
    await asyncio.gather(stage(), stage())
    assert await session_db.scalar(select(func.count()).select_from(Notification)) == 1


@pytest.mark.asyncio
async def test_audit_admin_only_unified_and_private(client_for_tests, world, session_db):
    w = world; actor = w['accounts']['admin'][0].id; target = w['accounts']['s1'][0].id
    AuditEventsService(session_db).stage(actor, 'account_create', 'user', target)
    session_db.add(AccountAudit(actor_user_id=actor, target_user_id=target, action='reset', result='denied', correlation_id='a'*32))
    session_db.add(LifecycleAudit(actor_user_id=actor, object_type='course', object_id=98765, action='purge', correlation_id='b'*32))
    await session_db.commit()
    for name in ['s1', 's2', 't1', 't2']:
        assert (await client_for_tests.get('/audit-events', headers=headers(w, name))).status_code == 403
    r = await client_for_tests.get('/audit-events', headers=headers(w, 'admin'))
    assert r.status_code == 200, r.text
    body = r.json(); assert body['total'] == 3
    assert {n['source'] for n in body['items']} == {'event', 'account', 'lifecycle'}
    assert {n['result'] for n in body['items']} == {'success', 'denied'}
    assert all(n['correlation_id'] and n['created_at'] for n in body['items'])
    assert 'hashed_password' not in r.text and 'PRIVATE' not in r.text
    r = await client_for_tests.get('/audit-events', headers=headers(w, 'admin'), params={'offset':99})
    assert r.json()['total'] == 3 and r.json()['items'] == []
    r = await client_for_tests.get('/audit-events', headers=headers(w, 'admin'), params={'action':'purge', 'actor_user_id':actor})
    assert r.json()['total'] == 1 and r.json()['items'][0]['object_id'] == 98765


@pytest.mark.asyncio
@pytest.mark.parametrize('url', ['/notifications?limit=0', '/notifications?offset=-1', '/audit-events?limit=101'])
async def test_validation(client_for_tests, world, url):
    assert (await client_for_tests.get(url, headers=headers(world, 'admin'))).status_code == 422


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['homework', 'lesson', 'review'])
async def test_domain_rollback_after_event(client_for_tests, world, session_db, monkeypatch, operation):
    w = world
    if operation == 'review':
        r = await client_for_tests.post(route(w, '/submit'), headers=headers(w))
        version = r.json()['version']
    original = NotificationsRepository.stage
    async def fail(self, *args, **kwargs):
        await original(self, *args, **kwargs)
        raise RuntimeError('injected after stage')
    monkeypatch.setattr(NotificationsRepository, 'stage', fail)
    before = await session_db.scalar(select(func.count()).select_from(Notification))
    count = await session_db.scalar(select(func.count()).select_from(Homework))
    if operation == 'homework':
        async def action():
            await client_for_tests.post('/homeworks', headers=headers(w, 't1'), data={
                'lesson_id': w['lessons'][0].id, 'student_user_id': w['accounts']['s1'][0].id, 'title': 'rollback'})
    elif operation == 'lesson':
        async def action():
            await client_for_tests.patch(f"/lessons/{w['lessons'][0].id}", headers=headers(w, 't1'), json={'status':'cancelled'})
    else:
        async def action():
            await client_for_tests.patch(route(w, '/teacher'), headers=headers(w, 't1'), json={'expected_version':version, 'grade':5})
    with pytest.raises(RuntimeError, match='injected'):
        await action()
    assert await session_db.scalar(select(func.count()).select_from(Notification)) == before
    if operation == 'homework':
        assert await session_db.scalar(select(func.count()).select_from(Homework)) == count
    elif operation == 'lesson':
        from src.modules.lessons.models import Lesson
        assert await session_db.scalar(select(Lesson.status).where(Lesson.id == w['lessons'][0].id)) == 'scheduled'
    else:
        assert await session_db.scalar(select(HomeworkSubmission.status).where(HomeworkSubmission.id == w['submissions'][0].id)) == 'submitted'


@pytest.mark.asyncio
async def test_concurrent_identical_patch(client_for_tests, world, session_db, config_fix):
    w = world
    from src.modules.lessons.depends import get_lessons_service
    from src.modules.lessons.models_dto import UpdateLessonRequestDTO
    async def cancel():
        async with config_fix.db_connection.session_local() as session:
            await get_lessons_service(session).update_lesson(w['accounts']['t1'][0].id,
                w['lessons'][0].id, UpdateLessonRequestDTO(status='cancelled'))
    await asyncio.gather(cancel(), cancel())
    assert (await inbox(client_for_tests, w))['total'] == 1


@pytest.mark.asyncio
async def test_unauthenticated_and_inactive(client_for_tests, world, session_db):
    for url in ['/notifications', '/notifications/unread', '/notifications/1/target', '/audit-events']:
        assert (await client_for_tests.get(url)).status_code == 401
    from src.modules.users.models import User
    await session_db.execute(update(User).where(User.id == world['accounts']['s1'][0].id).values(is_active=False))
    await session_db.commit()
    assert (await client_for_tests.get('/notifications', headers=headers(world))).status_code == 401


@pytest.mark.asyncio
async def test_real_sensitive_actions_audited(client_for_tests, world):
    w = world
    data = {'teacher_user_id':w['accounts']['t2'][0].id, 'student_user_id':w['accounts']['s2'][0].id}
    r = await client_for_tests.post('/teacher_students', headers=headers(w, 'admin'), json=data)
    assert r.status_code == 200, r.text
    r = await client_for_tests.get('/audit-events', headers=headers(w, 'admin'), params={'action':'teacher_student_link'})
    assert r.json()['total'] == 1
    assert r.json()['items'][0]['object_type'] == 'teacher_student'
    r = await client_for_tests.post('/auth/register', headers=headers(w, 'admin'), json={
        'username':'t13_synthetic_teacher', 'role':'teacher', 'first_name':'Synthetic', 'last_name':'T13'})
    assert r.status_code == 200, r.text
    created = r.json()
    r = await client_for_tests.get('/audit-events', headers=headers(w, 'admin'), params={'action':'account_create'})
    assert r.json()['total'] == 1
    assert r.json()['items'][0]['object_id'] == created['id']


@pytest.mark.asyncio
async def test_internal_lesson_event_retry_is_deduplicated(client_for_tests, world, session_db):
    service = NotificationsService(session_db)
    for _ in range(2):
        await service.lesson_event(world['lessons'][0].id, 'lesson_rescheduled')
    await session_db.commit()
    assert (await inbox(client_for_tests, world))['total'] == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['link', 'account'])
async def test_audit_is_atomic_with_sensitive_action(client_for_tests, world, session_db, monkeypatch, operation):
    from src.modules.audit_events.models import AuditEvent
    from src.modules.users.models import User
    original = AuditEventsService.stage
    def fail(self, *args, **kwargs):
        original(self, *args, **kwargs)
        raise RuntimeError('injected audit failure')
    monkeypatch.setattr(AuditEventsService, 'stage', fail)
    w = world
    with pytest.raises(RuntimeError, match='injected audit failure'):
        if operation == 'link':
            await client_for_tests.post('/teacher_students', headers=headers(w, 'admin'), json={
                'teacher_user_id':w['accounts']['t2'][0].id, 'student_user_id':w['accounts']['s2'][0].id})
        else:
            await client_for_tests.post('/auth/register', headers=headers(w, 'admin'), json={
                'username':'t13_rollback_teacher', 'role':'teacher', 'first_name':'Synthetic', 'last_name':'Test'})
    assert await session_db.scalar(select(func.count()).select_from(AuditEvent)) == 0
    if operation == 'link':
        assert await session_db.scalar(select(TeacherStudent.id).where(
            TeacherStudent.teacher_id == w['teachers'][1].id, TeacherStudent.student_id == w['students'][1].id)) is None
    else:
        assert await session_db.scalar(select(User.id).where(User.username == 't13_rollback_teacher')) is None
