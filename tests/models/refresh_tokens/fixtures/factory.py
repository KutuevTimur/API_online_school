import secrets
from datetime import timedelta, UTC, datetime

from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.refresh_tokens.models import RefreshToken
from src.models.refresh_tokens.models_dto import RefreshTokenDTO
from tests.models.refresh_tokens.fixtures.models_dto import CreateRefreshTokenFixtureDTO
from tests.models.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.models.users.fixtures.factory import create_user_factory


def _generate_unique_token() -> str:
    return secrets.token_urlsafe(64)


async def create_refresh_token_factory(
    session_db: AsyncSession,
    crypto_context: CryptContext,
    new_refresh_token: CreateRefreshTokenFixtureDTO,
) -> RefreshTokenDTO:
    if new_refresh_token.user_id is None:
        new_user = await create_user_factory(
            session_db=session_db,
            crypto_context=crypto_context,
            new_user=CreateUserFixtureDTO(),
        )
        new_refresh_token.user_id = new_user.id

    token = RefreshToken(
        user_id=new_refresh_token.user_id,
        token=new_refresh_token.token if new_refresh_token.token else _generate_unique_token(),
        is_revoked=new_refresh_token.is_revoked,
        expires_at=new_refresh_token.expires_at
        if new_refresh_token.expires_at else
        datetime.now(UTC) + timedelta(days=30)
    )
    session_db.add(token)
    await session_db.commit()
    await session_db.refresh(token)

    return RefreshTokenDTO.model_validate(token)

