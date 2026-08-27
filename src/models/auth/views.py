from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from src.models.auth.auth_service import AuthService
from src.models.auth.depends import get_auth_service, get_token_service, get_current_user
from src.models.auth.models_dto import TokenResponse, RefreshTokenRequest, LogoutRequest, LogoutResponse
from src.models.auth.token_service import TokenService
from src.models.users.depends import get_user_service
from src.models.users.models_dto import UsersDTO, RegisterUserRequestDTO
from src.models.users.service import UsersService

router = APIRouter(prefix="/auth")


@router.post("/register", response_model=UsersDTO, status_code=status.HTTP_200_OK)
async def register_user(
    data: RegisterUserRequestDTO,
    user_service: UsersService = Depends(get_user_service)
):
    """
    :raises UserAlreadyExists: 409 Если email занят
    """
    return await user_service.create_user(new_user=data)


@router.post('/login', response_model=TokenResponse, tags=["Authentication"], )
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service)
):
    return await auth_service.login(
        username=form_data.username,
        password=form_data.password
    )


@router.post('/refresh_tokens', response_model=TokenResponse, tags=["Authentication"], )
async def refresh_tokens(
    token: RefreshTokenRequest,
    token_service: TokenService = Depends(get_token_service)
):
    return await token_service.refresh_tokens(token.refresh_token)


@router.post('/logout', response_model=LogoutResponse)
async def logout(
    token: LogoutRequest,
    current_user: UsersDTO = Depends(get_current_user), # проверка на наличие прав
    token_service: TokenService = Depends(get_token_service)
):
    """Удаляет refresh токен только который передаётся"""
    return await token_service.logout(token.refresh_token)



