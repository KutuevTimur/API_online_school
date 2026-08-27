from fastapi import Depends

from src.core.config import Config
from src.models.auth.auth_service import AuthService
from src.models.auth.login import oauth2_scheme
from src.models.auth.token_service import TokenService
from src.models.depends import get_config
from src.models.refresh_tokens.depends import get_refresh_tokens_service
from src.models.refresh_tokens.service import RefreshTokensService
from src.models.users.depends import get_user_service
from src.models.users.models_dto import UsersDTO
from src.models.users.service import UsersService


def get_token_service(
    config: Config = Depends(get_config),
    user_service: UsersService = Depends(get_user_service),
    refresh_token_service: RefreshTokensService = Depends(get_refresh_tokens_service),
) -> TokenService:
    return TokenService(
        config=config,
        users_service=user_service,
        refresh_token_service=refresh_token_service,
    )


def get_auth_service(
    user_service: UsersService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
) -> AuthService:
    return AuthService(
        users_service=user_service,
        token_service=token_service
    )


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_service: AuthService = Depends(get_auth_service),
) -> UsersDTO:
    return await user_service.get_current_user(token)