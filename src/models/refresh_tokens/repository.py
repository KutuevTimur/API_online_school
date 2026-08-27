from datetime import datetime, UTC
from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base.database_model import BaseRepository
from src.models.refresh_tokens.models import RefreshToken
from src.models.refresh_tokens.models_dto import CreateRefreshTokenDTO


class RefreshTokenRepository(BaseRepository):

    def __init__(self, session: AsyncSession,):
        super().__init__(
            session,
            RefreshToken,
        )

    async def add_token(
        self,
        data: CreateRefreshTokenDTO,
    ) -> RefreshToken:
        return self.add(data)

    async def get_token(self, token: str) -> RefreshToken | None:
        result_db = await self.session.execute(
            select(RefreshToken)
            .where(RefreshToken.token == token)
        )
        return result_db.scalar_one_or_none()

    async def validate_refresh_token(self, refresh_token: str) -> RefreshToken | None:
        """
        :return int: user_id по указанному токену если он действителен
        """
        result = await self.session.execute(
            select(RefreshToken)
            .where(RefreshToken.token == refresh_token)
            .where(RefreshToken.expires_at >= datetime.now(UTC))
        )
        db_token = result.scalar_one_or_none()
        return db_token

    async def set_is_revoked(self, refresh_token: str) -> RefreshToken | None:
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.token == refresh_token)
            .values(is_revoked=True,)
            .returning(RefreshToken)
        )
        db_token = result.scalar_one_or_none()
        return db_token

    async def update_refresh_token(
        self,
        old_token: str,
        new_token: str,
        expires_at: Optional[datetime] = None
    ) -> RefreshToken | None:
        result = await self.session.execute(
            update(RefreshToken)
            .where(RefreshToken.token == old_token)
            .values(
                token=new_token,
                expires_at=expires_at
            )
            .returning(RefreshToken)
        )
        db_token = result.scalar_one_or_none()
        return db_token

    async def delete_expires_tokens(self) -> List[RefreshToken]:
        result_db = await self.session.execute(
            delete(RefreshToken)
            .where(RefreshToken.expires_at < datetime.now())
            .returning(RefreshToken)
        )
        return result_db.scalars().all()

    async def delete_token(self, token: str) -> RefreshToken | None:
        result_db = await self.session.execute(
            delete(RefreshToken)
            .where(RefreshToken.token == token)
            .returning(RefreshToken)
        )
        return result_db.scalar_one_or_none()