"""T03: public serialization and authorization failures on isolated PostgreSQL."""
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from jose import jwt
from sqlalchemy import select, update, func

from src.modules.auth.exception import InvalidCredentials
from src.modules.auth.token_service import TokenService
from src.modules.refresh_tokens.models import RefreshToken
from src.modules.refresh_tokens.service import token_digest
from src.modules.users.models import User, UserRole
from src.modules.users.models_dto import UserDTO, UserResponse
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO

# Artificial signing key, unrelated to any runtime secret.
TEST_KEY = "t03-artificial-jwt-key-for-regression-tests"


def assert_public(value):
    if isinstance(value, dict):
        assert "hashed_password" not in value
        for nested in value.values():
            assert_public(nested)
    elif isinstance(value, list):
        for nested in value:
            assert_public(nested)


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/auth/register", "/auth/register_by_admin", "/auth/register-by-admin"])
@pytest.mark.parametrize("role", [UserRole.STUDENT, UserRole.TEACHER])
async def test_registration_public_contract(path, role, client_for_tests, create_user_fixture, config_fix, session_db):
    _, token = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.ADMIN))
    data = dict(email="t03@mail.com", username="t03_user", password="t03_password",
                first_name="Test", last_name="Synthetic", role=role.value)
    if path != "/auth/register":
        data["password_for_admin"] = config_fix.env.password_for_admin
    response = await client_for_tests.post(path, headers={"Authorization": f"Bearer {token}"}, json=data)
    assert response.status_code == 200
    assert_public(response.json())
    public = UserResponse.model_validate(response.json())
    assert set(response.json()) == set(UserResponse.model_fields) | {"activation_link", "expires_at"}
    stored = await session_db.get(User, public.id)
    internal = UserDTO.model_validate(stored)
    assert internal.hashed_password and internal.is_active
    assert internal.hashed_password != data["password"]


@pytest.mark.asyncio
@pytest.mark.parametrize("method,path", [
    ("POST", "/auth/change_password"), ("POST", "/auth/change-password"),
    ("PATCH", "/auth/change_password"), ("PATCH", "/auth/change-password"),
])
async def test_password_alias_public_contract(method, path, client_for_tests, create_user_fixture):
    user, token = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.STUDENT, password="old_t03_password"))
    response = await client_for_tests.request(method, f"{path}/{user.id}",
        headers={"Authorization": f"Bearer {token}"}, json={"current_password": "old_t03_password", "new_password": "new_t03_password"})
    assert response.status_code == 200
    assert_public(response.json())
    assert set(response.json()) == set(UserResponse.model_fields)
    response = await client_for_tests.post("/auth/login", data={"username": user.username, "password": "new_t03_password"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_public_openapi(app_fastapi):
    schema = app_fastapi.openapi()
    def check_schema(node):
        if isinstance(node, dict):
            if "$ref" in node:
                check_schema(schema["components"]["schemas"][node["$ref"].split("/")[-1]])
            assert "hashed_password" not in node.get("properties", {})
            for key, value in node.items():
                if key != "$ref":
                    check_schema(value)
        elif isinstance(node, list):
            for value in node:
                check_schema(value)
    for path in schema["paths"].values():
        for operation in path.values():
            for response in operation["responses"].values():
                check_schema(response)
    # Hidden aliases also explicitly use the safe DTO.
    for route in app_fastapi.routes:
        if getattr(route, "path", "").startswith(("/auth/register", "/auth/change")):
            assert issubclass(route.response_model, UserResponse)


@pytest.mark.asyncio
async def test_active_then_disabled_all_auth_paths(client_for_tests, create_user_fixture, session_db):
    user, token = await create_user_fixture(new_user=CreateUserFixtureDTO(password="t03_password"))
    login = await client_for_tests.post("/auth/login", data={"username": user.username, "password": "t03_password"})
    assert login.status_code == 200
    me = await client_for_tests.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert_public(me.json())
    refresh = await client_for_tests.post("/auth/refresh_tokens", json={"refresh_token": login.json()["refresh_token"]})
    assert refresh.status_code == 200
    await session_db.execute(update(User).where(User.id == user.id).values(is_active=False))
    await session_db.commit()
    before = await session_db.scalar(select(func.count()).select_from(RefreshToken))
    responses = [
        await client_for_tests.post("/auth/login", data={"username": user.username, "password": "t03_password"}),
        await client_for_tests.get("/users/me", headers={"Authorization": f"Bearer {token}"}),
        await client_for_tests.post("/auth/refresh_tokens", json={"refresh_token": refresh.json()["refresh_token"]}),
    ]
    for response in responses:
        assert response.status_code == 401
        assert response.json() == {"detail": "Invalid credentials"}
    assert await session_db.scalar(select(func.count()).select_from(RefreshToken)) == before
    stored = await session_db.scalar(select(RefreshToken).where(RefreshToken.digest == token_digest(refresh.json()["refresh_token"])))
    assert not stored.is_revoked


BAD_CLAIMS = [
    {"sub": "1"}, {"exp": 4102444800},
    {"sub": "abc", "exp": 4102444800}, {"sub": "0", "exp": 4102444800},
    {"sub": "-1", "exp": 4102444800}, {"sub": True, "exp": 4102444800},
    {"sub": 1, "exp": 4102444800}, {"sub": "1.2", "exp": 4102444800},
    {"sub": "2147483648", "exp": 4102444800},
    {"sub": "1", "exp": 1}, {"sub": "1", "exp": "4102444800"},
    {"sub": "1", "exp": True}, {"sub": "1", "exp": None},
    {"sub": "1", "exp": float("inf")}, {"sub": "1", "exp": float("nan")},
    {"sub": "1", "exp": []}, {"sub": None, "exp": 4102444800},
]


@pytest.mark.asyncio
@pytest.mark.parametrize("claims", BAD_CLAIMS)
async def test_invalid_claims_http_401(claims, client_for_tests, config_fix, monkeypatch):
    monkeypatch.setattr(config_fix.env, "secret_key", TEST_KEY)
    token = jwt.encode(claims, TEST_KEY, algorithm=config_fix.tokens.algorithm)
    response = await client_for_tests.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.asyncio
@pytest.mark.parametrize("kind", ["signature", "algorithm", "malformed", "missing_user"])
async def test_invalid_token_http_401(kind, client_for_tests, config_fix, monkeypatch):
    monkeypatch.setattr(config_fix.env, "secret_key", TEST_KEY)
    algorithm = "HS512" if config_fix.tokens.algorithm != "HS512" else "HS256"
    token = jwt.encode({"sub": "2147483647", "exp": 4102444800},
        "wrong-artificial-key" if kind == "signature" else TEST_KEY,
        algorithm=algorithm if kind == "algorithm" else config_fix.tokens.algorithm)
    if kind == "malformed":
        token = "malformed.jwt"
    response = await client_for_tests.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.asyncio
async def test_missing_login_and_refresh(client_for_tests):
    response = await client_for_tests.post("/auth/login", data={"username": "missing_t03", "password": "wrong"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}
    response = await client_for_tests.post("/auth/refresh_tokens", json={"refresh_token": "missing_synthetic_token"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.asyncio
async def test_refresh_missing_user_service(session_db, config_fix):
    from src.modules.refresh_tokens.service import RefreshTokensService
    from src.modules.refresh_tokens.repository import RefreshTokenRepository
    service = RefreshTokensService(RefreshTokenRepository(session_db), session_db, config_fix)
    with pytest.raises(InvalidCredentials):
        await service.lock_user(2147483647)


@pytest.mark.asyncio
async def test_nested_public_profiles(client_for_tests, create_user_fixture):
    teacher, token = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.ADMIN))
    student, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(role=UserRole.STUDENT))
    for path in ["/users/me", "/users/students", "/users/teachers", f"/users/{student.id}", f"/users/{teacher.id}"]:
        response = await client_for_tests.get(path, headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        assert_public(response.json())


@pytest.mark.asyncio
async def test_wrong_password_generic_failure(client_for_tests, create_user_fixture):
    user, _ = await create_user_fixture(new_user=CreateUserFixtureDTO(password="t03_password"))
    response = await client_for_tests.post("/auth/login", data={"username": user.username, "password": "wrong"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}
