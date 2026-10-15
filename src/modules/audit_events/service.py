from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.audit_events.repository import AuditEventsRepository
from src.modules.audit_events.models_dto import AuditEventResponseDTO
from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.check_permission.service import ObjectPermissionService
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.users.models import UserRole


class AuditEventsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = AuditEventsRepository(session)

    def stage(self, actor: int, action: str, kind: str, target: int) -> None:
        # Fixed schema deliberately has no arbitrary metadata/payload field.
        self.repo.add(dict(actor_user_id=actor, action=action, object_type=kind,
                           object_id=target, result="success", correlation_id=uuid4().hex))

    async def page(self, user_id: int, limit: int, offset: int,
                   actor_user_id: int | None, action: str | None) -> PaginationResponseDTO[AuditEventResponseDTO]:
        actor = await ObjectPermissionService(self.session).actor(user_id)
        if actor.role != UserRole.ADMIN:
            raise PermissionErrorService()
        rows, total = await self.repo.page(limit, offset, actor_user_id, action)
        return PaginationResponseDTO(items=[AuditEventResponseDTO.model_validate(r) for r in rows],
                                     total=total, limit=limit, offset=offset)
