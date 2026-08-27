import pytest
from sqlalchemy import select

from src.models.auth.models_dto import TokenResponse, RefreshTokenRequest, LogoutRequest
from src.models.refresh_tokens.models import RefreshToken
from src.models.users.models import Users
from src.models.users.models_dto import RegisterUserRequestDTO, UsersDTO
from tests.models.refresh_tokens.fixtures.fixtures import create_refresh_token_fixture
from tests.models.refresh_tokens.fixtures.models_dto import CreateRefreshTokenFixtureDTO
from tests.models.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.helpers.functions import comparison_models


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_register_user(
        self, 
        session_db,
        client_for_tests,
    ):
        response = await client_for_tests.post(
            "/auth/register",
            json=RegisterUserRequestDTO(
                email="test_@mail.com",
                username="test_user",
                password="test_password",
            ).model_dump(),
        )

        assert response.status_code == 200

        new_user = UsersDTO.model_validate(response.json())

        result_db = await session_db.execute(select(Users).where(Users.id == new_user.id))
        user_from_db = result_db.scalar_one_or_none()
        assert user_from_db

        assert comparison_models(new_user, user_from_db)


    @pytest.mark.asyncio
    async def test_login(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
    ):
        user, accesses_token = await create_user_fixture(
            new_user=CreateUserFixtureDTO(
                password="test_password",
            )
        )
        response = await client_for_tests.post(
            "/auth/login",
            data={
                'username': user.username,
                'password': "test_password"
            }
        )

        assert response.status_code == 200

        token = TokenResponse.model_validate(response.json())

        result_db = await session_db.execute(select(RefreshToken).where(RefreshToken.token == token.refresh_token))
        token_db = result_db.scalar_one_or_none()
        assert token_db

    @pytest.mark.asyncio
    async def test_refresh_tokens(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_refresh_token_fixture,
    ):
        old_token = await create_refresh_token_fixture(new_refresh_token=CreateRefreshTokenFixtureDTO())

        response = await client_for_tests.post(
            "/auth/refresh_tokens",
            json=RefreshTokenRequest(
                refresh_token=old_token.token,
            ).model_dump(),
        )

        assert response.status_code == 200

        new_token = TokenResponse.model_validate(response.json())

        # старый должен быть помечен
        result_db = await session_db.execute(select(RefreshToken).where(RefreshToken.token == old_token.token))
        token_db: RefreshToken = result_db.scalar_one_or_none()
        assert token_db.is_revoked

        # новый токен есть
        result_db = await session_db.execute(select(RefreshToken).where(RefreshToken.token == new_token.refresh_token))
        token_db = result_db.scalar_one_or_none()
        assert token_db

    @pytest.mark.asyncio
    async def test_login(
        self,
        session_db,
        client_for_tests,
        create_user_fixture,
        create_refresh_token_fixture,
    ):
        user, accesses_token = await create_user_fixture(new_user=CreateUserFixtureDTO())

        token = await create_refresh_token_fixture(
            new_refresh_token=CreateRefreshTokenFixtureDTO(
                user_id=user.id,
            )
        )

        response = await client_for_tests.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {accesses_token}"},
            json=LogoutRequest(
                refresh_token=token.token,
            ).model_dump(),
        )

        assert response.status_code == 200

        result_db = await session_db.execute(select(RefreshToken).where(RefreshToken.token == token.token))
        token_db: RefreshToken = result_db.scalar_one_or_none()
        assert not token_db
