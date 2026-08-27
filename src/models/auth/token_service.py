from datetime import timedelta, UTC, datetime
from typing import Dict

from jose import jwt, JWTError

from src.core.config import Config
from src.models.auth.exception import InvalidJWTToken
from src.models.auth.models_dto import TokenResponse, LogoutResponse
from src.models.refresh_tokens.exception import RefreshTokenNotFound
from src.models.refresh_tokens.service import RefreshTokensService
from src.models.users.exception import UserNotFound
from src.models.users.service import UsersService


class TokenService:

    def __init__(
        self,
        config: Config,
        users_service: UsersService,
        refresh_token_service: RefreshTokensService,
    ):
        self.config = config
        self.users_service = users_service
        self.refresh_token_service = refresh_token_service
        pass

    def _encode_access_token(
        self,
        to_encode: dict,
    ) -> str:
        """
        :param to_encode: Данные для кодирования
        """

        return jwt.encode(
            to_encode,
            self.config.env.secret_key,
            algorithm=self.config.tokens.algorithm
        )


    def decode_access_token(self, token: str) -> int:
        """
        :return: user_id
        :raises InvalidJWTToken: невалидный токен
        """

        try:
            payload = jwt.decode(
                token,
                self.config.env.secret_key,
                algorithms=[self.config.tokens.algorithm],
                options={"verify_exp": True}
            )

            # Извлекаем ID пользователя
            user_id: int = int(payload.get("sub"))

            if user_id is None:
                raise InvalidJWTToken()

            return user_id

        except JWTError as e:
            raise InvalidJWTToken() from e

    def generate_data_for_access_token(self, user_id: int) -> Dict[str, str]:
        return {"sub": str(user_id)}

    def create_access_token(
        self,
        user_id: int,
        expires_delta: timedelta = None
    ) -> str:
        to_encode = self.generate_data_for_access_token(user_id)

        # Установка времени истечения токена
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=self.config.tokens.access_token_expire_minutes)

        # Добавляем поле с временем истечения
        to_encode.update({"exp": expire})

        return self._encode_access_token(to_encode)

    async def create_token_response(self, user_id: int) -> TokenResponse:
        new_access_token = self.create_access_token(user_id=user_id)
        new_refresh_token = await self.refresh_token_service.create_token(user_id)

        return TokenResponse(access_token=new_access_token, refresh_token=new_refresh_token.token, token_type="bearer")

    async def refresh_tokens(self, old_refresh_token: str) -> TokenResponse:
        """
        :raise RefreshTokenNotFound:
        :raise UserNotFound:
        """
        old_refresh_token_obj = await self.refresh_token_service.validate_refresh_token(old_refresh_token)

        if not old_refresh_token_obj:
            raise RefreshTokenNotFound()

        user = await self.users_service.get_user_by_id(old_refresh_token_obj.user_id)

        if not user:
            raise UserNotFound()

        await self.refresh_token_service.set_is_revoked(old_refresh_token)

        return await self.create_token_response(user_id=user.id)

    async def logout(self, refresh_token: str) -> LogoutResponse:
        await self.refresh_token_service.delete_token(refresh_token)
        return LogoutResponse(success=True)