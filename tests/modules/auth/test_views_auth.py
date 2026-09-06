import pytest
from sqlalchemy import select

from src.modules.auth.models_dto import (
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
    ChangePasswordRequestDTO,
)
from src.modules.refresh_tokens.models import RefreshToken
from src.modules.users.models import User, UserRole
from src.modules.users.models_dto import RegisterUserRequestDTO, RegisterUserByAdminRequestDTO, UserDTO
from tests.modules.refresh_tokens.fixtures.fixtures import create_refresh_token_fixture
from tests.modules.refresh_tokens.fixtures.models_dto import CreateRefreshTokenFixtureDTO
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.helpers.functions import comparison_models


class TestsForSuccess:

    @pytest.mark.asyncio
    async def test_register_user(
        self, 
        session_db,
        client_for_tests,
        create_user_fixture,
    ):
        user, accesses_token = await create_user_fixture(
            new_user=CreateUserFixtureDTO(
                password="test_password",
                role=UserRole.TEACHER,
            )
        )
        response = await client_for_tests.post(
            "/auth/register",
            headers={"Authorization": f"Bearer {accesses_token}"},
            json=RegisterUserRequestDTO(
                email="test_@mail.com",
                username="test_user",
                password="test_password",
                first_name="test_first_name",
                last_name="test_last_name",
                role=UserRole.TEACHER,
            ).model_dump(),
        )

        assert response.status_code == 200

        new_user = UserDTO.model_validate(response.json())

        result_db = await session_db.execute(select(User).where(User.id == new_user.id))
        user_from_db = result_db.scalar_one_or_none()
        assert user_from_db

        assert comparison_models(new_user, user_from_db)

    @pytest.mark.asyncio
    async def test_register_user_by_admin_success(
        self,
        session_db,
        client_for_tests,
        config_fix,
    ):
        response = await client_for_tests.post(
            "/auth/register_by_admin",
            json=RegisterUserByAdminRequestDTO(
                email="admin_created@mail.com",
                username="admin_created_user",
                password="admin_created_password",
                first_name="Admin",
                last_name="Created",
                role=UserRole.TEACHER,
                password_for_admin=config_fix.env.password_for_admin,
            ).model_dump(),
        )

        assert response.status_code == 200

        new_user = UserDTO.model_validate(response.json())

        result_db = await session_db.execute(select(User).where(User.id == new_user.id))
        user_from_db = result_db.scalar_one_or_none()
        assert user_from_db

        assert comparison_models(new_user, user_from_db)

    @pytest.mark.asyncio
    async def test_register_user_by_admin_invalid_password(
        self,
        client_for_tests,
    ):
        response = await client_for_tests.post(
            "/auth/register_by_admin",
            json=RegisterUserByAdminRequestDTO(
                email="admin_created_fail@mail.com",
                username="admin_created_fail_user",
                password="admin_created_fail_password",
                first_name="Admin",
                last_name="Fail",
                role=UserRole.TEACHER,
                password_for_admin="wrong_admin_password",
            ).model_dump(),
        )

        assert response.status_code == 403
        assert response.json() == {"detail": "Not permission"}

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
    async def test_logout(
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

    @pytest.mark.asyncio
    async def test_change_password_by_self_student(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        student, access_token = await create_user_fixture(
            new_user=CreateUserFixtureDTO(
                password="old_student_password",
                role=UserRole.STUDENT,
            )
        )

        response = await client_for_tests.post(
            f"/auth/change_password/{student.id}",
            headers={"Authorization": f"Bearer {access_token}"},
            json=ChangePasswordRequestDTO(new_password="new_student_password").model_dump(),
        )

        assert response.status_code == 200

        # Проверяем, что можно успешно залогиниться с новым паролем
        login_response = await client_for_tests.post(
            "/auth/login",
            data={
                "username": student.username,
                "password": "new_student_password",
            },
        )
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_by_teacher_for_student(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        teacher, teacher_token = await create_user_fixture(
            new_user=CreateUserFixtureDTO(role=UserRole.TEACHER)
        )
        student, _ = await create_user_fixture(
            new_user=CreateUserFixtureDTO(
                password="initial_student_pwd",
                role=UserRole.STUDENT,
            )
        )

        response = await client_for_tests.post(
            f"/auth/change_password/{student.id}",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json=ChangePasswordRequestDTO(new_password="reset_by_teacher_pwd").model_dump(),
        )

        assert response.status_code == 200

        login_response = await client_for_tests.post(
            "/auth/login",
            data={
                "username": student.username,
                "password": "reset_by_teacher_pwd",
            },
        )
        assert login_response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_forbidden_for_other_student(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        student_1, token_1 = await create_user_fixture(
            new_user=CreateUserFixtureDTO(role=UserRole.STUDENT)
        )
        student_2, _ = await create_user_fixture(
            new_user=CreateUserFixtureDTO(role=UserRole.STUDENT)
        )

        response = await client_for_tests.post(
            f"/auth/change_password/{student_2.id}",
            headers={"Authorization": f"Bearer {token_1}"},
            json=ChangePasswordRequestDTO(new_password="hacked_pwd").model_dump(),
        )

        assert response.status_code == 403
        assert response.json() == {"detail": "Not permission"}

    @pytest.mark.asyncio
    async def test_change_password_unauthorized(
        self,
        client_for_tests,
    ):
        response = await client_for_tests.post(
            "/auth/change_password/1",
            json={"new_password": "no_auth_password"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_not_found(
        self,
        client_for_tests,
        create_user_fixture,
    ):
        teacher, teacher_token = await create_user_fixture(
            new_user=CreateUserFixtureDTO(role=UserRole.TEACHER)
        )

        response = await client_for_tests.post(
            "/auth/change_password/99999",
            headers={"Authorization": f"Bearer {teacher_token}"},
            json=ChangePasswordRequestDTO(new_password="some_pwd").model_dump(),
        )

        assert response.status_code == 404
        assert response.json() == {"detail": "Not found data"}
