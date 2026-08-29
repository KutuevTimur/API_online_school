from fastapi import Depends

from src.core.database.database import get_db
from src.modules.depends import get_config
from src.modules.refresh_tokens.repository import RefreshTokenRepository
from src.modules.refresh_tokens.service import RefreshTokensService


def get_refresh_tokens_service(
    session = Depends(get_db),
    config = Depends(get_config),
) -> RefreshTokensService:
    return RefreshTokensService(
        token_repo=RefreshTokenRepository(session=session),
        session_db=session,
        config=config,
    )