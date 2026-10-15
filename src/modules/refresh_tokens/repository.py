from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.base.repository_model import BaseRepository
from src.modules.refresh_tokens.models import RefreshToken
from src.modules.refresh_tokens.models_dto import CreateRefreshTokenDTO


class RefreshTokenRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session, RefreshToken)

    async def add_token(self, data: CreateRefreshTokenDTO) -> RefreshToken:
        return self.add(data)

    async def get_token(self, digest: str, *, lock: bool = False) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.digest == digest)
        if lock:
            stmt = stmt.with_for_update().execution_options(populate_existing=True)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def revoke_family(self, user_id: int, family_id: str) -> None:
        await self.session.execute(update(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.family_id == family_id
        ).values(is_revoked=True))

    async def revoke_user(self, user_id: int) -> None:
        await self.session.execute(update(RefreshToken).where(
            RefreshToken.user_id == user_id
        ).values(is_revoked=True))
