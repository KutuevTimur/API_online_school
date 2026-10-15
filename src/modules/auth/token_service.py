from datetime import timedelta, UTC, datetime
from math import isfinite

from jose import jwt, JWTError

from src.core.config import Config
from src.modules.auth.exception import InvalidJWTToken
from src.modules.auth.models_dto import TokenResponse, LogoutResponse
from src.modules.refresh_tokens.service import RefreshTokensService
from src.modules.users.service import UsersService


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


    def decode_access_token(self, token: str) -> tuple[int, int]:
        """
        :return: user_id
        :raises InvalidJWTToken: невалидный токен
        """

        try:
            payload = jwt.decode(
                token,
                self.config.env.secret_key,
                algorithms=[self.config.tokens.algorithm],
                options={"verify_exp": False, "require_exp": True, "require_sub": True}
            )
            # Verify expiration here to reject coercible strings/bools and non-finite values.
            exp = payload["exp"]
            if (isinstance(exp, bool) or not isinstance(exp, (int, float))
                    or not isfinite(exp) or exp <= datetime.now(UTC).timestamp()):
                raise InvalidJWTToken()
            subject = payload["sub"]
            if not isinstance(subject, str) or not subject.isascii() or not subject.isdecimal():
                raise InvalidJWTToken()
            user_id = int(subject)
            # PostgreSQL User PK is a signed INTEGER.
            if not 0 < user_id <= 2**31 - 1:
                raise InvalidJWTToken()
            version = payload.get("ver")
            if type(version) is not int or version < 0:
                raise InvalidJWTToken()
            return user_id, version
        except (JWTError, TypeError, ValueError, OverflowError) as exc:
            raise InvalidJWTToken() from exc

    def generate_data_for_access_token(self, user_id: int) -> dict[str, str | int]:
        return {"sub": str(user_id)}

    def create_access_token(
        self,
        user_id: int,
        expires_delta: timedelta | None = None,
        auth_version: int = 0
    ) -> str:
        to_encode = self.generate_data_for_access_token(user_id)
        to_encode["ver"] = auth_version

        # Установка времени истечения токена
        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(minutes=self.config.tokens.access_token_expire_minutes)

        # Добавляем поле с временем истечения
        to_encode.update({"exp": expire})

        return self._encode_access_token(to_encode)

    async def create_token_response(self, user_id: int) -> TokenResponse:
        service = self.refresh_token_service
        try:
            user = await service.lock_user(user_id)
            access = self.create_access_token(user.id, auth_version=user.auth_version)
            raw = await service.issue(user.id)
            await service.session_db.commit()
            return TokenResponse(access_token=access, refresh_token=raw, token_type="bearer")
        except Exception:
            await service.session_db.rollback()
            raise

    async def refresh_tokens(self, old_refresh_token: str) -> TokenResponse:
        raw, user_id, version = await self.refresh_token_service.rotate(old_refresh_token)
        return TokenResponse(access_token=self.create_access_token(user_id, auth_version=version),
                             refresh_token=raw, token_type="bearer")

    async def logout(self, refresh_token: str, user_id: int) -> LogoutResponse:
        await self.refresh_token_service.logout(refresh_token, user_id)
        return LogoutResponse(success=True)
