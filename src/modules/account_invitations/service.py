import secrets
from uuid import uuid4
from datetime import datetime, timedelta, UTC
from src.modules.account_invitations.repository import InvitationRepository
from src.modules.account_invitations.models_dto import InvitationResponse, ConsumeInvitationResponse
from src.modules.account_invitations.exception import InvalidInvitation
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.refresh_tokens.repository import RefreshTokenRepository
from src.modules.refresh_tokens.service import token_digest
from src.modules.users.models import User, UserRole
from src.modules.users.models_dto import UserDTO
from src.modules.users.service import UsersService


class InvitationService:
    def __init__(self, users: UsersService):
        self.users = users
        self.session = users.session_db
        self.repo = InvitationRepository(self.session)

    async def stage_issue(self, user: User, purpose: str, actor: UserDTO) -> InvitationResponse:
        raw = secrets.token_urlsafe(48)
        expires = datetime.now(UTC) + timedelta(hours=72 if purpose == "invite" else 1)
        await self.repo.invalidate(user.id, purpose)
        await self.repo.insert(user_id=user.id, purpose=purpose, digest=token_digest(raw),
                               expires_at=expires, consumed=False)
        await self.repo.audit(actor_user_id=actor.id, target_user_id=user.id,
                              action=purpose + "_issued", correlation_id=uuid4().hex)
        await self.session.flush()
        # Fragment keeps the secret out of HTTP request URLs/access logs. T14 supplies the page.
        return InvitationResponse(activation_link=f"/{'activate' if purpose == 'invite' else 'reset-password'}#token={raw}", expires_at=expires)

    async def issue(self, user_id: int, purpose: str, actor: UserDTO) -> InvitationResponse:
        try:
            if actor.role not in {UserRole.ADMIN, UserRole.TEACHER}:
                raise PermissionErrorService()
            if actor.role != UserRole.ADMIN and (purpose != "invite" or not await self.repo.is_linked(actor.id, user_id)):
                raise PermissionErrorService()
            user = await self.users.users_repo.lock_user(user_id)
            allowed = user is not None and user.is_active and (
                (purpose == "invite" and not user.is_activated) or
                (purpose == "reset" and user.is_activated))
            if not allowed:
                # Same shape/status for absent, disabled and ineligible targets; no secret.
                await self.repo_denied_audit(actor, user, purpose)
                await self.session.commit()
                return InvitationResponse()
            result = await self.stage_issue(user, purpose, actor)
            await self.session.commit()
            return result
        except Exception:
            await self.session.rollback()
            raise

    async def repo_denied_audit(self, actor: UserDTO, user: User | None, purpose: str) -> None:
        if user is not None:
            await self.repo.audit(actor_user_id=actor.id, target_user_id=user.id,
                                  action=purpose + "_issued", result="denied", correlation_id=uuid4().hex)

    async def consume(self, raw: str, purpose: str, new_password: str) -> ConsumeInvitationResponse:
        try:
            token = await self.repo.find(token_digest(raw))
            if token is None:
                raise InvalidInvitation()
            # Same order as refresh/password mutations: user first, then token.
            user = await self.users.users_repo.lock_user(token.user_id)
            token = await self.repo.find(token_digest(raw), lock=True)
            if (user is None or not user.is_active or token.consumed or token.purpose != purpose
                    or token.expires_at <= datetime.now(UTC)
                    or (purpose == "invite" and user.is_activated)
                    or (purpose == "reset" and not user.is_activated)):
                raise InvalidInvitation()
            user.hashed_password = self.users._get_hash_password(new_password)
            user.is_activated = True
            user.auth_version += 1
            token.consumed = True
            await self.repo.invalidate(user.id, purpose)
            await RefreshTokenRepository(self.session).revoke_user(user.id)
            await self.repo.audit(actor_user_id=user.id, target_user_id=user.id,
                                  action=purpose + "_consumed", correlation_id=uuid4().hex)
            await self.session.commit()
            return ConsumeInvitationResponse(success=True)
        except Exception:
            await self.session.rollback()
            raise
