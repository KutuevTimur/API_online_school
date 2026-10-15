from src.modules.auth.exception import InvalidCredentials, require_active_user
from src.modules.auth.models_dto import TokenResponse
from src.modules.auth.token_service import TokenService
from src.modules.users.models_dto import UserDTO
from src.modules.users.service import UsersService


class AuthService:

    def __init__(
        self,
        users_service: UsersService,
        token_service: TokenService,
    ):
        self.users_service = users_service
        self.token_service = token_service

    async def get_current_user(
        self,
        token: str
    ) -> UserDTO:
        """
        :raises InvalidJWTToken: невалидный токен
        :raises InvalidCredentials: missing or inactive account
        """

        user_id, version = self.token_service.decode_access_token(token)
        result = await self.users_service.get_user_by_id(user_id)

        user = require_active_user(result)
        if user.auth_version != version:
            raise InvalidCredentials()
        return user

    async def login(
        self,
        username: str,
        password: str
    ) -> TokenResponse:

        user = await self.users_service.get_user_by_username(username)

        user = require_active_user(user)
        user = await self.token_service.refresh_token_service.lock_user(user.id)

        if not self.users_service.verify_password(
            password,
            user.hashed_password
        ):
            raise InvalidCredentials()

        return await self.token_service.create_token_response(user_id=user.id)

    async def change_password(
        self,
        user_id: int,
        new_password: str,
        current_password: str,
    ) -> UserDTO:
        return await self.users_service.change_password(
            user_id=user_id,
            new_password=new_password,
            current_password=current_password,
        )
