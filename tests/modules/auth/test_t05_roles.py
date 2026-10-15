import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from sqlalchemy import select, func
from src.modules.users.models import User, UserRole
from src.modules.teacher_students.models import TeacherStudent
from src.modules.teacher_students.repository import TeacherStudentRepository
from src.modules.users.depends import get_user_service
from src.modules.users.models_dto import RegisterUserRequestDTO
from src.tools.bootstrap_admin import bootstrap_admin, BootstrapInput
from tests.helpers import test_crypto_context
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


def payload(role='student'):
    return dict(email='t05@mail.com', username='t05_new', password='synthetic-password',
                first_name='Synthetic', last_name='Test', role=role)


def auth(token):
    return {'Authorization': f'Bearer {token}'}


@pytest.mark.asyncio
@pytest.mark.parametrize('actor_role', list(UserRole))
@pytest.mark.parametrize('target_role', list(UserRole))
async def test_creation_matrix(actor_role, target_role, create_user_fixture, client_for_tests, session_db):
    _, token = await create_user_fixture(new_user=CreateUserFixtureDTO(role=actor_role))
    response = await client_for_tests.post('/auth/register', headers=auth(token), json=payload(target_role.value))
    allowed = (actor_role == UserRole.ADMIN and target_role != UserRole.ADMIN) or (actor_role == UserRole.TEACHER and target_role == UserRole.STUDENT)
    assert response.status_code == (200 if allowed else 403)
    assert (await session_db.scalar(select(func.count()).select_from(TeacherStudent))) == int(actor_role == UserRole.TEACHER and allowed)
    if allowed:
        assert 'hashed_password' not in response.json()


@pytest.mark.asyncio
@pytest.mark.parametrize('path', ['/auth/register_by_admin', '/auth/register-by-admin'])
async def test_no_master_bypass(path, config_fix, client_for_tests, create_user_fixture):
    data = {**payload(), 'password_for_admin': config_fix.env.password_for_admin}
    assert (await client_for_tests.post(path, json=data)).status_code == 401
    _, token = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.TEACHER))
    assert (await client_for_tests.post(path, json=data, headers=auth(token))).status_code == 403


@pytest.mark.asyncio
async def test_link_second_teacher_unique_and_access(create_user_fixture, client_for_tests, session_db, not_open_session_db):
    admin, at = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.ADMIN))
    t1, tt = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.TEACHER))
    t2, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, st = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.STUDENT))
    for token in [tt, st]:
        assert (await client_for_tests.post('/teacher_students', headers=auth(token), json=dict(teacher_user_id=t1.id, student_user_id=student.id))).status_code == 403
    for teacher in [t1, t2]:
        response = await client_for_tests.post('/teacher_students', headers=auth(at), json=dict(teacher_user_id=teacher.id, student_user_id=student.id))
        assert response.status_code == 200
        assert response.json() == dict(teacher_user_id=teacher.id, student_user_id=student.id, active=True)
    rows = (await session_db.scalars(select(TeacherStudent))).all()
    async def link():
        async with not_open_session_db() as session:
            await TeacherStudentRepository(session).link(rows[0].teacher_id, rows[0].student_id)
            await session.commit()
    await asyncio.gather(link(), link())
    assert await session_db.scalar(select(func.count()).select_from(TeacherStudent)) == 2
    from sqlalchemy import update
    await session_db.execute(update(TeacherStudent).where(TeacherStudent.id==rows[0].id).values(ended_at=func.now()))
    await session_db.commit()
    response = await client_for_tests.post('/teacher_students', headers=auth(at), json=dict(teacher_user_id=t1.id, student_user_id=student.id))
    assert response.status_code == 200
    await session_db.refresh(rows[0])
    assert rows[0].ended_at is None
    assert await session_db.scalar(select(func.count()).select_from(TeacherStudent)) == 2
    assert (await client_for_tests.post('/teacher_students', headers=auth(at), json=dict(teacher_user_id=student.id, student_user_id=admin.id))).status_code == 404
    assert (await client_for_tests.patch(f'/users/{admin.id}', headers=auth(tt), json={'username':'escalated'})).status_code == 404
    assert (await client_for_tests.patch(f'/users/{student.id}', headers=auth(tt), json={'is_active':False})).status_code == 403


@pytest.mark.asyncio
async def test_creation_rolls_back_link_failure(create_user_fixture, session_db, app_fastapi, config_fix, monkeypatch):
    teacher, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.TEACHER))
    service = get_user_service(SimpleNamespace(app=app_fastapi), session_db, config_fix)
    monkeypatch.setattr(TeacherStudentRepository, 'link', AsyncMock(side_effect=RuntimeError('injected')))
    with pytest.raises(RuntimeError, match='injected'):
        await service.create_user(RegisterUserRequestDTO(**payload()), actor=teacher)
    assert await session_db.scalar(select(User.id).where(User.username=='t05_new')) is None
    assert await session_db.scalar(select(func.count()).select_from(TeacherStudent)) == 0


@pytest.mark.asyncio
async def test_bootstrap_concurrent_refuses_second(not_open_session_db, session_db):
    data = BootstrapInput(username='first_admin', email='first@mail.com', password='synthetic-password')
    async def run():
        async with not_open_session_db() as session:
            return await bootstrap_admin(session, data, test_crypto_context)
    assert sorted(await asyncio.gather(run(), run())) == [False, True]
    assert await run() is False
    stored = await session_db.scalar(select(User).where(User.role==UserRole.ADMIN))
    assert test_crypto_context.verify(data.password, stored.hashed_password)
    assert stored.is_active
    assert await session_db.scalar(select(func.count()).select_from(User).where(User.role==UserRole.ADMIN)) == 1


@pytest.mark.asyncio
async def test_duplicate_student_does_not_assign_existing(create_user_fixture, client_for_tests, session_db):
    teacher, token = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.STUDENT, email='t05@mail.com'))
    response = await client_for_tests.post('/auth/register', headers=auth(token), json=payload())
    assert response.status_code == 409
    assert await session_db.scalar(select(func.count()).select_from(TeacherStudent)) == 0
    assert await session_db.scalar(select(User.id).where(User.id==student.id)) == student.id


@pytest.mark.asyncio
async def test_missing_teacher_profile_refused(create_user_fixture, client_for_tests, session_db):
    from sqlalchemy import delete
    from src.modules.teachers.models import Teacher
    teacher, token = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.TEACHER))
    await session_db.execute(delete(Teacher).where(Teacher.user_id==teacher.id))
    await session_db.commit()
    assert (await client_for_tests.post('/auth/register', headers=auth(token), json=payload())).status_code == 403
    assert await session_db.scalar(select(User.id).where(User.username=='t05_new')) is None


@pytest.mark.asyncio
async def test_interactive_bootstrap(monkeypatch, capsys, session_db):
    from src.tools import bootstrap_admin as cli
    inputs = iter(['cli_admin', 'cli_admin@mail.com'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    monkeypatch.setattr(cli.getpass, 'getpass', lambda _: 'synthetic-cli-password')
    await cli.main()
    output = capsys.readouterr().out
    assert output.strip() == 'Admin created'
    assert 'synthetic-cli-password' not in output
    assert await session_db.scalar(select(User.role).where(User.username=='cli_admin')) == UserRole.ADMIN
