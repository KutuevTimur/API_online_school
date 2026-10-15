from fastapi import APIRouter, Depends, Query
from src.modules.check_permission.depends import get_current_admin_user
from src.modules.users.models_dto import UserDTO
from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.audit_events.models_dto import AuditEventResponseDTO
from src.modules.audit_events.depends import get_audit_events_service
from src.modules.audit_events.service import AuditEventsService

router = APIRouter(prefix="/audit-events", tags=["Admin audit"])


@router.get("", response_model=PaginationResponseDTO[AuditEventResponseDTO], status_code=200)
async def audit_events(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
    actor_user_id: int | None = Query(None, gt=0), action: str | None = Query(None, max_length=32),
    user: UserDTO = Depends(get_current_admin_user),
    service: AuditEventsService = Depends(get_audit_events_service)) -> PaginationResponseDTO[AuditEventResponseDTO]:
    return await service.page(user.id, limit, offset, actor_user_id, action)
