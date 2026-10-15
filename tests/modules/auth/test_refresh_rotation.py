"""T04 PostgreSQL regression tests, including independent-session races."""
import asyncio
from datetime import datetime, UTC, timedelta

import pytest
from jose import jwt
from sqlalchemy import select, update

from src.modules.auth.exception import InvalidCredentials
from src.modules.refresh_tokens.models import RefreshToken
from src.modules.refresh_tokens.repository import RefreshTokenRepository
from src.modules.refresh_tokens.service import RefreshTokensService, token_digest
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO

pytestmark = pytest.mark.asyncio


async def login(client, user):
    response = await client.post('/auth/login', data={'username': user.username, 'password': 'rotation_password'})
    assert response.status_code == 200
    return response.json()


async def refresh(client, raw):
    return await client.post('/auth/refresh_tokens', json={'refresh_token': raw})


async def test_rotation_replay_family_and_secrets(client_for_tests, create_user_fixture, session_db, caplog):
    user, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(password='rotation_password'))
    first = await login(client_for_tests, user)
    other = await login(client_for_tests, user)
    second = await refresh(client_for_tests, first['refresh_token'])
    assert second.status_code == 200
    assert set(second.json()) == {'access_token', 'refresh_token', 'token_type'}
    assert (await refresh(client_for_tests, first['refresh_token'])).status_code == 401
    assert (await refresh(client_for_tests, second.json()['refresh_token'])).status_code == 401
    assert (await refresh(client_for_tests, other['refresh_token'])).status_code == 200
    rows = (await session_db.scalars(select(RefreshToken))).all()
    assert len({r.digest for r in rows}) == len(rows)
    for row in rows:
        assert not hasattr(row, 'token')
        assert len(row.digest) == 64
    assert first['refresh_token'] not in caplog.text
    assert second.json()['refresh_token'] not in caplog.text


@pytest.mark.parametrize('state', ['expired', 'revoked', 'inactive'])
async def test_invalid_refresh(state, client_for_tests, create_user_fixture, session_db):
    from src.modules.users.models import User
    user, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(password='rotation_password'))
    tokens = await login(client_for_tests, user)
    if state == 'inactive':
        await session_db.execute(update(User).where(User.id == user.id).values(is_active=False))
    else:
        values = {'is_revoked': True} if state == 'revoked' else {'expires_at': datetime.now(UTC) - timedelta(seconds=1)}
        await session_db.execute(update(RefreshToken).values(**values))
    await session_db.commit()
    assert (await refresh(client_for_tests, tokens['refresh_token'])).status_code == 401


async def test_concurrent_sessions(config_fix, create_user_fixture, client_for_tests):
    user, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(password='rotation_password'))
    tokens = await login(client_for_tests, user)
    gate = asyncio.Event()
    async def run():
        async with config_fix.db_connection.session_local() as session:
            service = RefreshTokensService(RefreshTokenRepository(session), session, config_fix)
            await gate.wait()
            try:
                return await service.rotate(tokens['refresh_token'])
            except InvalidCredentials:
                return None
    jobs = [asyncio.create_task(run()) for _ in range(2)]
    gate.set()
    results = await asyncio.wait_for(asyncio.gather(*jobs), timeout=10)
    successes = [r for r in results if r is not None]
    assert len(successes) == 1
    # The loser confirms replay and revokes the winner's descendant.
    assert (await refresh(client_for_tests, successes[0][0])).status_code == 401
    async with config_fix.db_connection.session_local() as session:
        rows = (await session.scalars(select(RefreshToken).where(RefreshToken.user_id == user.id))).all()
        assert len(rows) == 2
        assert all(row.is_revoked for row in rows)


async def test_insert_failure_rolls_back(config_fix, create_user_fixture, client_for_tests, monkeypatch):
    user, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(password='rotation_password'))
    tokens = await login(client_for_tests, user)
    async with config_fix.db_connection.session_local() as session:
        service = RefreshTokensService(RefreshTokenRepository(session), session, config_fix)
        async def fail(*args):
            raise RuntimeError('synthetic insert failure')
        monkeypatch.setattr(service, 'issue', fail)
        with pytest.raises(RuntimeError, match='synthetic insert failure'):
            await service.rotate(tokens['refresh_token'])
    async with config_fix.db_connection.session_local() as session:
        rows = (await session.scalars(select(RefreshToken))).all()
        assert len(rows) == 1
        assert rows[0].is_revoked is False
    assert (await refresh(client_for_tests, tokens['refresh_token'])).status_code == 200


async def test_logout_ownership_and_idempotence(create_user_fixture, client_for_tests):
    a, access_a = await create_user_fixture(new_user=CreateUserFixtureDTO(password='rotation_password'))
    b, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(password='rotation_password'))
    ta, tb = await login(client_for_tests, a), await login(client_for_tests, b)
    async def logout(raw):
        return await client_for_tests.post('/auth/logout', json={'refresh_token': raw}, headers={'Authorization': f'Bearer {access_a}'})
    assert (await logout(tb['refresh_token'])).status_code == 200
    assert (await refresh(client_for_tests, tb['refresh_token'])).status_code == 200
    for raw in [ta['refresh_token'], ta['refresh_token'], 'unknown-synthetic']:
        response = await logout(raw)
        assert response.status_code == 200
        assert response.json() == {'success': True}
    assert (await refresh(client_for_tests, ta['refresh_token'])).status_code == 401
    assert (await client_for_tests.post('/auth/logout', json={'refresh_token': 'unknown'})).status_code == 401


async def test_password_revokes_only_target(create_user_fixture, client_for_tests, session_db):
    a, access_a = await create_user_fixture(new_user=CreateUserFixtureDTO(password='rotation_password'))
    b, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(password='rotation_password'))
    ta, extra, tb = await login(client_for_tests, a), await login(client_for_tests, a), await login(client_for_tests, b)
    response = await client_for_tests.post(f'/auth/change_password/{a.id}', json={'current_password': 'rotation_password', 'new_password': 'new_rotation_password'}, headers={'Authorization': f'Bearer {access_a}'})
    assert response.status_code == 200
    for access in [access_a, ta['access_token']]:
        assert (await client_for_tests.get('/users/me', headers={'Authorization': f'Bearer {access}'})).status_code == 401
    for raw in [ta['refresh_token'], extra['refresh_token']]:
        assert (await refresh(client_for_tests, raw)).status_code == 401
    assert (await refresh(client_for_tests, tb['refresh_token'])).status_code == 200
    assert (await client_for_tests.get('/users/me', headers={'Authorization': f"Bearer {tb['access_token']}"})).status_code == 200
    response = await client_for_tests.post('/auth/login', data={'username': a.username, 'password': 'new_rotation_password'})
    assert response.status_code == 200
    assert (await client_for_tests.get('/users/me', headers={'Authorization': f"Bearer {response.json()['access_token']}"})).status_code == 200
    rows = (await session_db.scalars(select(RefreshToken).where(RefreshToken.user_id == a.id))).all()
    assert sum(not row.is_revoked for row in rows) == 1


@pytest.mark.parametrize('version', [None, True, -1, '0', 1.5, 999])
async def test_invalid_or_legacy_access_version(version, create_user_fixture, client_for_tests, config_fix):
    user, _ = await create_user_fixture(new_user=CreateUserFixtureDTO())
    claims = {'sub': str(user.id), 'exp': datetime.now(UTC) + timedelta(minutes=5)}
    if version is not None:
        claims['ver'] = version
    token = jwt.encode(claims, config_fix.env.secret_key, algorithm=config_fix.tokens.algorithm)
    assert (await client_for_tests.get('/users/me', headers={'Authorization': f'Bearer {token}'})).status_code == 401


async def test_password_failure_rolls_back_revocation(config_fix, create_user_fixture, client_for_tests, monkeypatch):
    from src.modules.users.repository import UsersRepository
    from src.modules.users.service import UsersService
    from types import SimpleNamespace
    user, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(password='rotation_password'))
    tokens = await login(client_for_tests, user)
    async with config_fix.db_connection.session_local() as session:
        async def fail(_self, user_id):
            raise RuntimeError('synthetic revoke failure')
        monkeypatch.setattr(RefreshTokenRepository, 'revoke_user', fail)
        # Exercise the actual password scenario with irrelevant collaborators omitted.
        service = object.__new__(UsersService)
        service.users_repo = UsersRepository(session)
        service.session_db = session
        service.cr_context = SimpleNamespace(hash=lambda _: 'synthetic-unused-hash', verify=lambda plain, hashed: plain == 'rotation_password')
        with pytest.raises(RuntimeError, match='synthetic revoke failure'):
            await service.change_password(user.id, 'synthetic-new-password', 'rotation_password')
    assert (await refresh(client_for_tests, tokens['refresh_token'])).status_code == 200
    assert (await login(client_for_tests, user))['access_token']


async def test_teacher_cannot_reset_target(create_user_fixture, client_for_tests):
    from src.modules.users.models import UserRole
    teacher, teacher_access = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.TEACHER, password='rotation_password'))
    student, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(password='rotation_password'))
    own, target = await login(client_for_tests, teacher), await login(client_for_tests, student)
    response = await client_for_tests.post(f'/auth/change-password/{student.id}', json={'current_password': 'rotation_password', 'new_password': 'reset_rotation_password'}, headers={'Authorization': f'Bearer {teacher_access}'})
    assert response.status_code == 403
    assert (await refresh(client_for_tests, target['refresh_token'])).status_code == 200
    assert (await client_for_tests.get('/users/me', headers={'Authorization': f"Bearer {target['access_token']}"})).status_code == 200
    assert (await refresh(client_for_tests, own['refresh_token'])).status_code == 200
    response = await client_for_tests.post('/auth/login', data={'username': student.username, 'password': 'rotation_password'})
    assert response.status_code == 200
