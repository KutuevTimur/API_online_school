from datetime import datetime
from src.modules.base.orm_dto import ORMDTO


class AuditEventResponseDTO(ORMDTO):
    source: str
    id: int
    actor_user_id: int
    action: str
    object_type: str
    object_id: int
    result: str
    correlation_id: str
    created_at: datetime
