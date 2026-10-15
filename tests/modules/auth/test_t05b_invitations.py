import asyncio
from datetime import datetime, timedelta, UTC
from types import SimpleNamespace
from unittest.mock import AsyncMock
import pytest
from sqlalchemy import select, update, func
from src.modules.account_invitations.models import AccountInvitation, AccountAudit, AuthRateLimit
from src.modules.account_invitations.repository import InvitationRepository, RateLimitRepository
from src.modules.account_invitations.service import InvitationService
from src.modules.auth.exception import InvalidCredentials
from src.modules.users.depends import get_user_service
from src.modules.users.models import User, UserRole
from src.modules.refresh_tokens.repository import RefreshTokenRepository
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO

pytestmark = pytest.mark.asyncio


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def raw(response):
    return response['activation_link'].split('#token=')[1]


async def create(client, token, role='student', username='invited'):
    r = await client.post('/auth/register', headers=auth(token), json=dict(
        username=username, role=role, first_name='Synthetic', last_name='Test'))
    assert r.status_code == 200, r.text
    return r.json()


async def consume(client, secret, purpose='invite', password='new-password'):
    return await client.post('/account_invitations/consume', json=dict(
        token=secret, purpose=purpose, new_password=password))


async def issue(client, token, uid, purpose='invite'):
    return await client.post('/account_invitations/issue', headers=auth(token),
                             json=dict(user_id=uid, purpose=purpose))


@pytest.mark.parametrize('role', ['student', 'teacher'])
async def test_activation_nullable_email_and_username_login(role, client_for_tests, create_user_fixture, session_db):
    _, admin_token = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.ADMIN))
    data = await create(client_for_tests, admin_token, role)
    assert data['email'] is None
    assert 71.9 < (datetime.fromisoformat(data['expires_at']) - datetime.now(UTC)).total_seconds()/3600 <= 72
    row = await session_db.scalar(select(AccountInvitation))
    assert raw(data) not in row.digest
    assert len(row.digest) == 64
    user = await session_db.get(User, data['id'])
    assert not user.is_activated and user.is_active
    r = await client_for_tests.post('/auth/login', data=dict(username='invited', password='new-password'))
    assert r.status_code == 401
    assert (await consume(client_for_tests, raw(data))).status_code == 200
    assert (await consume(client_for_tests, raw(data))).status_code == 401
    assert (await client_for_tests.post('/auth/login', data=dict(username='invited', password='new-password'))).status_code == 200
    assert await session_db.scalar(select(func.count()).select_from(AccountAudit)) == 2


async def test_teacher_only_reinvites_own_pending(client_for_tests, create_user_fixture, session_db):
    _, t1 = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.TEACHER))
    _, t2 = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.TEACHER))
    data = await create(client_for_tests, t1)
    assert (await issue(client_for_tests, t2, data['id'])).status_code == 403
    assert (await issue(client_for_tests, t1, data['id'], 'reset')).status_code == 403
    replacement = (await issue(client_for_tests, t1, data['id'])).json()
    assert (await consume(client_for_tests, raw(data))).status_code == 401
    assert (await consume(client_for_tests, raw(replacement))).status_code == 200
    assert (await issue(client_for_tests, t1, data['id'])).json()['activation_link'] is None
    assert (await issue(client_for_tests, t1, data['id'], 'reset')).status_code == 403


@pytest.mark.parametrize('fault', ['expired', 'disabled', 'purpose', 'missing'])
async def test_bad_token_generic(fault, client_for_tests, create_user_fixture, session_db):
    _, admin = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.ADMIN))
    data = await create(client_for_tests, admin)
    if fault == 'expired':
        await session_db.execute(update(AccountInvitation).values(expires_at=datetime.now(UTC)-timedelta(seconds=1)))
    if fault == 'disabled':
        await session_db.execute(update(User).where(User.id==data['id']).values(is_active=False))
    await session_db.commit()
    r = await consume(client_for_tests, 'unknown' if fault == 'missing' else raw(data), 'reset' if fault == 'purpose' else 'invite')
    assert r.status_code == 401 and r.json() == {'detail': 'Invalid credentials'}
    await session_db.refresh(await session_db.get(User, data['id']))
    assert not (await session_db.get(User, data['id'])).is_activated


async def test_reset_revokes_target_only(client_for_tests, create_user_fixture, session_db):
    _, admin = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.ADMIN))
    user, old_access = await create_user_fixture(new_user=CreateUserFixtureDTO(password='old-password'))
    other, other_access = await create_user_fixture(new_user=CreateUserFixtureDTO(password='old-password'))
    async def login(u):
        return (await client_for_tests.post('/auth/login', data=dict(username=u.username, password='old-password'))).json()
    tokens, other_tokens = await login(user), await login(other)
    first = (await issue(client_for_tests, admin, user.id, 'reset')).json()
    assert 0.99 < (datetime.fromisoformat(first['expires_at'])-datetime.now(UTC)).total_seconds()/3600 <= 1
    second = (await issue(client_for_tests, admin, user.id, 'reset')).json()
    assert (await consume(client_for_tests, raw(first), 'reset')).status_code == 401
    assert (await consume(client_for_tests, raw(second), 'reset')).status_code == 200
    assert (await client_for_tests.get('/users/me', headers=auth(old_access))).status_code == 401
    assert (await client_for_tests.post('/auth/refresh_tokens', json=dict(refresh_token=tokens['refresh_token']))).status_code == 401
    assert (await client_for_tests.get('/users/me', headers=auth(other_access))).status_code == 200
    assert (await client_for_tests.post('/auth/refresh_tokens', json=dict(refresh_token=other_tokens['refresh_token']))).status_code == 200
    assert (await client_for_tests.post('/auth/login', data=dict(username=user.username, password='new-password'))).status_code == 200
    assert (await client_for_tests.post('/auth/login', data=dict(username=user.email, password='new-password'))).status_code == 401


async def test_reset_missing_pending_disabled_same_response(client_for_tests, create_user_fixture, session_db):
    _, admin = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.ADMIN))
    pending = await create(client_for_tests, admin)
    user, _ = await create_user_fixture()
    await session_db.execute(update(User).where(User.id==user.id).values(is_active=False))
    await session_db.commit()
    responses = [await issue(client_for_tests, admin, uid, 'reset') for uid in [999999, pending['id'], user.id]]
    assert all(r.status_code == 200 and r.json()=={'activation_link':None,'expires_at':None} for r in responses)
    assert (await consume(client_for_tests, raw(pending), 'reset')).status_code == 401


async def test_concurrent_consume_and_failure_rollback(client_for_tests, create_user_fixture, not_open_session_db, app_fastapi, config_fix, monkeypatch):
    _, admin = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.ADMIN))
    data = await create(client_for_tests, admin)
    async def run():
        async with not_open_session_db() as session:
            service = InvitationService(get_user_service(SimpleNamespace(app=app_fastapi), session, config_fix))
            try:
                await service.consume(raw(data), 'invite', 'new-password')
                return True
            except InvalidCredentials:
                return False
    with monkeypatch.context() as patch:
        patch.setattr(RefreshTokenRepository, 'revoke_user', AsyncMock(side_effect=RuntimeError('injected')))
        with pytest.raises(RuntimeError, match='injected'):
            await run()
    # Failure left token pending; two actual DB sessions now race to consume it.
    assert sorted(await asyncio.gather(run(),run())) == [False,True]


async def test_creation_invite_failure_rolls_back(client_for_tests, create_user_fixture, session_db, monkeypatch):
    _, teacher = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.TEACHER))
    monkeypatch.setattr(InvitationRepository, 'insert', AsyncMock(side_effect=RuntimeError('injected')))
    with pytest.raises(RuntimeError, match='injected'):
        await create(client_for_tests, teacher)
    assert await session_db.scalar(select(User.id).where(User.username=='invited')) is None
    assert await session_db.scalar(select(func.count()).select_from(AccountAudit)) == 0


async def test_self_change_requires_current_password_and_no_cross_user(client_for_tests, create_user_fixture):
    user, access = await create_user_fixture(new_user=CreateUserFixtureDTO(password='old-password'))
    other, _ = await create_user_fixture()
    path = f'/auth/change_password/{user.id}'
    assert (await client_for_tests.post(path, headers=auth(access), json=dict(new_password='new-password'))).status_code == 422
    assert (await client_for_tests.post(path, headers=auth(access), json=dict(current_password='wrong',new_password='new-password'))).status_code == 401
    assert (await client_for_tests.post(f'/auth/change-password/{other.id}', headers=auth(access), json=dict(current_password='old-password',new_password='new-password'))).status_code == 403
    assert (await client_for_tests.post(path, headers=auth(access), json=dict(current_password='old-password',new_password='new-password'))).status_code == 200


@pytest.mark.parametrize('action', ['login','consume','issue'])
async def test_rate_limits_survive_failed_requests(action, client_for_tests, create_user_fixture):
    _, admin = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.ADMIN))
    async def attempt():
        if action=='login':
            return await client_for_tests.post('/auth/login', data=dict(username='missing',password='wrong'))
        if action=='consume':
            return await consume(client_for_tests,'missing')
        return await issue(client_for_tests,admin,999999,'reset')
    for _ in range(10):
        assert (await attempt()).status_code != 429
    assert (await attempt()).status_code == 429


async def test_rate_limit_atomic_windows(not_open_session_db):
    async def increment():
        async with not_open_session_db() as session:
            value = await RateLimitRepository(session).increment('synthetic', 10)
            await session.commit()
            return value
    assert sorted(await asyncio.gather(increment(),increment())) == [1,2]
    async with not_open_session_db() as session:
        assert await RateLimitRepository(session).increment('synthetic',11) == 1
        await session.commit()


async def test_username_email_cross_collision_is_unambiguous(client_for_tests, create_user_fixture):
    first, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(email='legacy@mail.com',password='first-password'))
    second, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(username='legacy@mail.com',password='second-password'))
    assert (await client_for_tests.post('/auth/login',data=dict(username='legacy@mail.com',password='first-password'))).status_code == 401
    assert (await client_for_tests.post('/auth/login',data=dict(username='legacy@mail.com',password='second-password'))).status_code == 200


async def test_self_change_invalidates_pending_reset(client_for_tests, create_user_fixture):
    _, admin = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.ADMIN))
    user, access = await create_user_fixture(new_user=CreateUserFixtureDTO(password='old-password'))
    reset = (await issue(client_for_tests, admin, user.id, 'reset')).json()
    changed = await client_for_tests.post(f'/auth/change_password/{user.id}', headers=auth(access),
                                         json=dict(current_password='old-password',new_password='changed-password'))
    assert changed.status_code == 200
    assert (await consume(client_for_tests,raw(reset),'reset')).status_code == 401


async def test_optional_email_can_be_removed(client_for_tests, create_user_fixture, session_db):
    user, access = await create_user_fixture()
    response = await client_for_tests.patch(f'/users/{user.id}', headers=auth(access), json={'email':None})
    assert response.status_code == 200
    assert (await session_db.get(User,user.id)).email is None


async def test_ip_limit_covers_different_token_identifiers(client_for_tests):
    for index in range(100):
        assert (await consume(client_for_tests,f'unknown-{index}')).status_code == 401
    response = await consume(client_for_tests,'another-unknown')
    assert response.status_code == 429 and int(response.headers['Retry-After']) > 0


async def test_reset_does_not_enable_disabled_account(client_for_tests, create_user_fixture, session_db):
    _, admin = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.ADMIN))
    user, _ = await create_user_fixture()
    reset = (await issue(client_for_tests,admin,user.id,'reset')).json()
    await session_db.execute(update(User).where(User.id==user.id).values(is_active=False))
    await session_db.commit()
    assert (await consume(client_for_tests,raw(reset),'reset')).status_code == 401
    assert not (await session_db.get(User,user.id)).is_active
