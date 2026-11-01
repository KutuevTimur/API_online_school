import pytest
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO

HEADERS = {'Origin': 'http://127.0.0.1:5173', 'X-LGG-Request': 'browser'}

@pytest.mark.asyncio
@pytest.mark.parametrize('origin', [None, 'null', 'https://foreign.example'])
async def test_csrf(client_for_tests, origin):
    headers = {'X-LGG-Request': 'browser'}
    if origin is not None:
        headers['Origin'] = origin
    for path in ['login', 'refresh', 'logout']:
        response = await client_for_tests.post('/auth/browser/' + path, headers=headers, json={})
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_simple_form(client_for_tests):
    for path in ['login', 'refresh', 'logout']:
        response = await client_for_tests.post('/auth/browser/' + path, headers={'Origin': HEADERS['Origin']}, data={'username': 'x', 'password': 'x'})
        assert response.status_code == 403

@pytest.mark.asyncio
@pytest.mark.parametrize('role', list(UserRole))
async def test_browser_session(client_for_tests, create_user_fixture, role):
    user, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(password='Synthetic-123', role=role))
    login = await client_for_tests.post('/auth/browser/login', headers=HEADERS, data={'username': user.username, 'password': 'Synthetic-123'})
    assert login.status_code == 200
    assert set(login.json()) == {'access_token', 'token_type'}
    cookie = login.headers['set-cookie']
    assert 'HttpOnly' in cookie and 'SameSite=lax' in cookie and 'Path=/api/auth/browser' in cookie
    raw = login.cookies['lgg_refresh']
    # ASGI transport uses internal paths while proxy exposes /api externally.
    refresh = await client_for_tests.post('/auth/browser/refresh', headers={**HEADERS, 'Cookie': 'lgg_refresh=' + raw}, json={})
    assert refresh.status_code == 200
    new_raw = refresh.cookies['lgg_refresh']
    assert raw != new_raw and 'refresh_token' not in refresh.json()
    me = await client_for_tests.get('/users/me', headers={'Authorization': 'Bearer ' + login.json()['access_token']})
    assert me.status_code == 200 and me.json()['role'] == role.value
    for _ in range(2):
        out = await client_for_tests.post('/auth/browser/logout', headers={**HEADERS, 'Cookie': 'lgg_refresh=' + new_raw}, json={})
        assert out.status_code == 200 and 'Max-Age=0' in out.headers['set-cookie']
    denied = await client_for_tests.post('/auth/browser/refresh', headers={**HEADERS, 'Cookie': 'lgg_refresh=' + new_raw}, json={})
    assert denied.status_code == 401

@pytest.mark.asyncio
async def test_replay_closes_family(client_for_tests, create_user_fixture):
    user, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(password='Synthetic-123'))
    login = await client_for_tests.post('/auth/browser/login', headers=HEADERS, data={'username': user.username, 'password': 'Synthetic-123'})
    raw = login.cookies['lgg_refresh']
    rotated = await client_for_tests.post('/auth/browser/refresh', headers={**HEADERS, 'Cookie': 'lgg_refresh=' + raw}, json={})
    assert rotated.status_code == 200
    for value in [raw, rotated.cookies['lgg_refresh']]:
        response = await client_for_tests.post('/auth/browser/refresh', headers={**HEADERS, 'Cookie': 'lgg_refresh=' + value}, json={})
        assert response.status_code == 401

@pytest.mark.asyncio
@pytest.mark.parametrize('path', ['login', 'refresh', 'logout'])
async def test_content_type_and_header_required(client_for_tests, path):
    for headers in [HEADERS, {'Origin': HEADERS['Origin']}, {**HEADERS, 'Content-Type': 'text/plain'}]:
        response = await client_for_tests.post('/auth/browser/' + path, headers=headers, content='{}')
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_browser_fixation_and_family_scope(client_for_tests, create_user_fixture):
    user, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(password='Synthetic-123'))
    async def login():
        response = await client_for_tests.post('/auth/browser/login', headers={**HEADERS, 'Cookie': 'lgg_refresh=attacker-chosen'}, data={'username': user.username, 'password': 'Synthetic-123'})
        assert response.status_code == 200
        return response.cookies['lgg_refresh']
    first, second = await login(), await login()
    assert first != second and first != 'attacker-chosen'
    await client_for_tests.post('/auth/browser/logout', headers={**HEADERS, 'Cookie': 'lgg_refresh=' + first}, json={})
    assert (await client_for_tests.post('/auth/browser/refresh', headers={**HEADERS, 'Cookie': 'lgg_refresh=' + second}, json={})).status_code == 200

@pytest.mark.asyncio
async def test_cookie_lifetime_uses_actual_expiry():
    from datetime import datetime, UTC, timedelta
    from types import SimpleNamespace
    from unittest.mock import AsyncMock
    from src.modules.auth.token_service import TokenService
    service = object.__new__(TokenService)
    service.refresh_token_service = SimpleNamespace(token_repo=SimpleNamespace(get_token=AsyncMock(return_value=SimpleNamespace(expires_at=datetime.now(UTC) + timedelta(seconds=10)))))
    assert 0 < await service.browser_cookie_max_age('synthetic') <= 10
