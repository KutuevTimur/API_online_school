import secrets
from datetime import datetime, timedelta, UTC
from typing import Callable, Awaitable, List

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import Config
from src.models.base.exception import ServiceException
from src.models.refresh_tokens.models import RefreshToken
from src.models.refresh_tokens.models_dto import RefreshTokenDTO, CreateRefreshTokenDTO
from src.models.refresh_tokens.repository import RefreshTokenRepository


class RefreshTokensService:

    def __init__(
        self,
        token_repo: RefreshTokenRepository,
        session_db: AsyncSession,
        config: Config,
    ):
        self.token_repo = token_repo
        self.session_db = session_db
        self.config = config

    def _generate_unique_token(self) -> str:
        return secrets.token_urlsafe(64)

    def _generate_expires_at(self) -> datetime:
        return datetime.now(UTC) + timedelta(
            days=self.config.tokens.refresh_token_expire_days
        )

    async def _execute_with_retry(
        self,
        operation: Callable[[], Awaitable[RefreshToken | None]]
    ) -> RefreshTokenDTO | None:
        for _ in range(5):
            try:
                token_orm = await operation()

                await self.session_db.commit()

                if token_orm:
                    await self.session_db.refresh(token_orm)
                    return RefreshTokenDTO.model_validate(token_orm)

                return None

            except IntegrityError:
                await self.session_db.rollback()

        raise ServiceException("Failed to generate token")

    async def create_token(self, user_id: int) -> RefreshTokenDTO | None:
        return await self._execute_with_retry(
            lambda: self.token_repo.add_token(
                data=CreateRefreshTokenDTO(
                    user_id=user_id,
                    token=self._generate_unique_token(),
                    expires_at=self._generate_expires_at(),
                )
            )
        )

    async def set_is_revoked(self, refresh_token: str) -> RefreshTokenDTO | None:
        """
        Не сохраняет данные!
        :return: Вернёт токен если есть что обновить.
        """
        token = await self.token_repo.set_is_revoked(refresh_token)
        return RefreshTokenDTO.model_validate(token) if token else None

    async def update_token(self, old_token: str) -> RefreshTokenDTO | None:
        return await self._execute_with_retry(
            lambda: self.token_repo.update_refresh_token(
                old_token=old_token,
                new_token=self._generate_unique_token(),
                expires_at=self._generate_expires_at(),
            )
        )

    async def get_token(self, refresh_token: str) -> RefreshTokenDTO | None:
        token = await self.token_repo.get_token(refresh_token)
        return RefreshTokenDTO.model_validate(token) if token else None

    async def validate_refresh_token(self, refresh_token: str) -> RefreshToken | None:
        """
        :return int: user_id по указанному токену если он действителен
        """
        return await self.token_repo.validate_refresh_token(refresh_token)

    async def delete_token(self, token: str) -> RefreshTokenDTO | None:
        result = await self.token_repo.delete_token(token)

        if result:
            await self.session_db.commit()
            return RefreshTokenDTO.model_validate(result)

        return None

    async def delete_expires_tokens(self) -> List[RefreshTokenDTO]:
        tokens = await self.token_repo.delete_expires_tokens()
        await self.session_db.commit()
        return [RefreshTokenDTO.model_validate(token) for token in tokens]