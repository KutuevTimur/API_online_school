import hashlib
import secrets
from datetime import datetime, timedelta, UTC
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config import Config
from src.modules.auth.exception import InvalidCredentials, require_active_user
from src.modules.refresh_tokens.models_dto import CreateRefreshTokenDTO
from src.modules.refresh_tokens.repository import RefreshTokenRepository
from src.modules.users.repository import UsersRepository
from src.modules.users.models import User


def token_digest(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class RefreshTokensService:
    def __init__(self, token_repo: RefreshTokenRepository, session_db: AsyncSession, config: Config):
        self.token_repo = token_repo
        self.session_db = session_db
        self.config = config

    async def lock_user(self, user_id: int) -> User:
        return require_active_user(await UsersRepository(self.session_db).lock_user(user_id))

    async def issue(self, user_id: int, family_id: str | None = None) -> str:
        """Stage one token; the scenario service owns commit/rollback."""
        raw = secrets.token_urlsafe(64)
        await self.token_repo.add_token(CreateRefreshTokenDTO(
            user_id=user_id, digest=token_digest(raw), family_id=family_id or uuid4().hex,
            expires_at=datetime.now(UTC) + timedelta(days=self.config.tokens.refresh_token_expire_days)))
        await self.session_db.flush()
        return raw

    async def rotate(self, raw: str) -> tuple[str, int, int]:
        try:
            token = await self.token_repo.get_token(token_digest(raw))
            if token is None:
                raise InvalidCredentials()
            # Every auth mutation locks user first, then token. This also serializes
            # password revocation and rotations of different generations in a family.
            user = await self.lock_user(token.user_id)
            token = await self.token_repo.get_token(token_digest(raw), lock=True)
            if token.is_revoked:
                await self.token_repo.revoke_family(user.id, token.family_id)
                await self.session_db.commit()  # Persist confirmed replay revocation.
                raise InvalidCredentials()
            if token.expires_at <= datetime.now(UTC):
                raise InvalidCredentials()
            token.is_revoked = True
            await self.session_db.flush()
            new_raw = await self.issue(user.id, token.family_id)
            result = (new_raw, user.id, user.auth_version)
            await self.session_db.commit()
            return result
        except Exception:
            await self.session_db.rollback()
            raise

    async def logout(self, raw: str, user_id: int) -> None:
        try:
            await self.lock_user(user_id)
            token = await self.token_repo.get_token(token_digest(raw), lock=True)
            if token is not None and token.user_id == user_id:
                await self.token_repo.revoke_family(user_id, token.family_id)
            await self.session_db.commit()
        except Exception:
            await self.session_db.rollback()
            raise

    async def browser_logout(self, raw: str) -> None:
        """Possession of the opaque cookie authorizes only its own family."""
        try:
            token = await self.token_repo.get_token(token_digest(raw))
            if token is not None:
                # Do not require an active account or a live access token to sign out.
                await UsersRepository(self.session_db).lock_user(token.user_id)
                token = await self.token_repo.get_token(token_digest(raw), lock=True)
                await self.token_repo.revoke_family(token.user_id, token.family_id)
            await self.session_db.commit()
        except Exception:
            await self.session_db.rollback()
            raise
