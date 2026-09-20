from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from src.core.config import Config
from src.modules.auth.auth_service import AuthService
from src.modules.auth.depends import get_auth_service, get_token_service, get_current_user
from src.modules.auth.models_dto import (
    TokenResponse,
    RefreshTokenRequest,
    LogoutRequest,
    LogoutResponse,
    ChangePasswordRequestDTO,
)
from src.modules.auth.token_service import TokenService
from src.modules.check_permission import (
    StudentPermissionService,
    get_current_teacher_user,
    get_current_user_with_target_permission,
)
from src.modules.depends import get_config
from src.modules.users.depends import get_user_service
from src.modules.users.models_dto import UserDTO, RegisterUserRequestDTO, RegisterUserByAdminRequestDTO
from src.modules.users.service import UsersService

router = APIRouter(prefix="/auth",  tags=["Authentication"])


@router.post("/register", response_model=UserDTO, status_code=status.HTTP_200_OK)
async def register_user(
    data: RegisterUserRequestDTO,
    current_user: UserDTO = Depends(get_current_teacher_user),
    user_service: UsersService = Depends(get_user_service),
):
    """
    :raises UserAlreadyExists: 409 Если email занят
    :raises PermissionErrorService: 403 Если создаёт нового пользователя не учитель
    """
    return await user_service.create_user(new_user=data)


@router.post("/register_by_admin", response_model=UserDTO, status_code=status.HTTP_200_OK)
@router.post("/register-by-admin", response_model=UserDTO, status_code=status.HTTP_200_OK, include_in_schema=False)
async def register_user_by_admin(
    data: RegisterUserByAdminRequestDTO,
    config: Config = Depends(get_config),
    user_service: UsersService = Depends(get_user_service),
):
    """
    Регистрация нового пользователя по мастер-паролю администратора (без требования токена current_user).
    :raises PermissionErrorService: 403 Если password_for_admin неверный
    :raises UserAlreadyExists: 409 Если email занят
    """
    StudentPermissionService.check_admin_password(
        provided_password=data.password_for_admin,
        expected_password=config.env.password_for_admin,
    )

    return await user_service.create_user(new_user=data)


@router.post("/change_password/{user_id}", response_model=UserDTO, status_code=status.HTTP_200_OK)
@router.post("/change-password/{user_id}", response_model=UserDTO, status_code=status.HTTP_200_OK, include_in_schema=False)
@router.patch("/change_password/{user_id}", response_model=UserDTO, status_code=status.HTTP_200_OK, include_in_schema=False)
@router.patch("/change-password/{user_id}", response_model=UserDTO, status_code=status.HTTP_200_OK, include_in_schema=False)
async def change_password(
    user_id: int,
    data: ChangePasswordRequestDTO,
    current_user: UserDTO = Depends(get_current_user_with_target_permission),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Смена пароля пользователя.
    :raises PermissionErrorService: 403 Если нет прав (не сам пользователь и не учитель)
    :raises NotFoundData: 404 Если пользователь не найден
    """
    return await auth_service.change_password(
        user_id=user_id,
        new_password=data.new_password,
    )


@router.post('/login', response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.login(
        username=form_data.username,
        password=form_data.password
    )


@router.post('/refresh_tokens', response_model=TokenResponse)
async def refresh_tokens(
    token: RefreshTokenRequest,
    token_service: TokenService = Depends(get_token_service)
):
    return await token_service.refresh_tokens(token.refresh_token)


@router.post('/logout', response_model=LogoutResponse)
async def logout(
    token: LogoutRequest,
    current_user: UserDTO = Depends(get_current_user),
    token_service: TokenService = Depends(get_token_service)
):
    """Удаляет refresh токен только который передаётся"""
    return await token_service.logout(token.refresh_token)
