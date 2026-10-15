from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

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
from src.modules.check_permission.depends import get_account_creator, get_current_admin_user
from src.modules.users.depends import get_user_service
from src.modules.users.models_dto import UserDTO, UserResponse, RegisterUserRequestDTO, RegisterUserByAdminRequestDTO
from src.modules.users.service import UsersService

from src.modules.account_invitations.models_dto import InvitationUserResponse
from src.modules.account_invitations.rate_limit import check_rate_limit
from src.modules.check_permission.exception import PermissionErrorService

router = APIRouter(prefix="/auth",  tags=["Authentication"])


@router.post("/register", response_model=InvitationUserResponse, status_code=status.HTTP_200_OK)
async def register_user(
    data: RegisterUserRequestDTO,
    current_user: UserDTO = Depends(get_account_creator),
    user_service: UsersService = Depends(get_user_service),
):
    """
    :raises UserAlreadyExists: 409 Если email занят
    :raises PermissionErrorService: 403 Если создаёт нового пользователя не учитель
    """
    return await user_service.create_user(new_user=data, actor=current_user)


@router.post("/register_by_admin", response_model=InvitationUserResponse, status_code=status.HTTP_200_OK)
@router.post("/register-by-admin", response_model=InvitationUserResponse, status_code=status.HTTP_200_OK, include_in_schema=False)
async def register_user_by_admin(
    data: RegisterUserByAdminRequestDTO,
    current_user: UserDTO = Depends(get_current_admin_user),
    user_service: UsersService = Depends(get_user_service),
):
    """Legacy alias: authenticated ADMIN only; master password grants no access."""
    return await user_service.create_user(new_user=data, actor=current_user)


@router.post("/change_password/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK)
@router.post("/change-password/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK, include_in_schema=False)
@router.patch("/change_password/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK, include_in_schema=False)
@router.patch("/change-password/{user_id}", response_model=UserResponse, status_code=status.HTTP_200_OK, include_in_schema=False)
async def change_password(
    request: Request,
    user_id: int,
    data: ChangePasswordRequestDTO,
    current_user: UserDTO = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """
    Смена собственного пароля с проверкой текущего.
    Чужой пароль, включая admin/teacher запрос, меняется только через reset-ссылку.
    """
    if current_user.id != user_id:
        raise PermissionErrorService()
    await check_rate_limit(request, "password", str(user_id))
    return await auth_service.change_password(
        user_id=user_id,
        new_password=data.new_password,
        current_password=data.current_password,
    )


@router.post('/login', response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    await check_rate_limit(request, "login", form_data.username)
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
    """Отзывает своё семейство сессии; повторный вызов возвращает 200."""
    return await token_service.logout(token.refresh_token, current_user.id)
