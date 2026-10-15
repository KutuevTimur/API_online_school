import secrets
from uuid import uuid4
from src.modules.refresh_tokens.service import token_digest
from datetime import timedelta, UTC, datetime

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.refresh_tokens.models import RefreshToken
from src.modules.refresh_tokens.models_dto import RefreshTokenDTO
from tests.modules.refresh_tokens.fixtures.models_dto import CreateRefreshTokenFixtureDTO
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.users.fixtures.factory import create_user_factory


class FixtureRefreshTokenDTO(RefreshTokenDTO):
    token: str


def _generate_unique_token() -> str:
    return secrets.token_urlsafe(64)


async def create_refresh_token_factory(
    session_db: AsyncSession,
    crypto_context: CryptContext,
    new_refresh_token: CreateRefreshTokenFixtureDTO,
) -> FixtureRefreshTokenDTO:
    if new_refresh_token.user_id is None:
        new_user = await create_user_factory(
            session_db=session_db,
            crypto_context=crypto_context,
            new_user=CreateUserFixtureDTO(),
        )
        new_refresh_token.user_id = new_user.id

    raw = new_refresh_token.token or _generate_unique_token()
    token = RefreshToken(
        user_id=new_refresh_token.user_id,
        digest=token_digest(raw),
        family_id=uuid4().hex,
        is_revoked=new_refresh_token.is_revoked,
        expires_at=new_refresh_token.expires_at
        if new_refresh_token.expires_at else
        datetime.now(UTC) + timedelta(days=30)
    )
    session_db.add(token)
    await session_db.commit()
    await session_db.refresh(token)

    return FixtureRefreshTokenDTO(**RefreshTokenDTO.model_validate(token).model_dump(), token=raw)

