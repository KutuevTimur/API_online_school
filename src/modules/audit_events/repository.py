from sqlalchemy import select, union_all, literal, func, true
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.base.repository_model import BaseRepository
from src.modules.audit_events.models import AuditEvent
from src.modules.account_invitations.models import AccountAudit
from src.modules.course_lifecycle.models import LifecycleAudit


class AuditEventsRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=AuditEvent)

    async def page(self, limit: int, offset: int, actor_user_id: int | None,
                   action: str | None) -> tuple[list[dict], int]:
        streams = []
        for model, source in [(AuditEvent, "event"), (AccountAudit, "account"), (LifecycleAudit, "lifecycle")]:
            kind = literal("user") if model is AccountAudit else model.object_type
            target = model.target_user_id if model is AccountAudit else model.object_id
            streams.append(select(literal(source).label("source"), model.id, model.actor_user_id,
                model.action, kind.label("object_type"), target.label("object_id"), model.result,
                model.correlation_id, model.created_at))
        combined = union_all(*streams).subquery()
        query = select(combined)
        if actor_user_id is not None:
            query = query.where(combined.c.actor_user_id == actor_user_id)
        if action is not None:
            query = query.where(combined.c.action == action)
        filtered = query.cte("filtered")
        page = select(filtered).order_by(filtered.c.created_at.desc(), filtered.c.source, filtered.c.id.desc()).limit(limit).offset(offset).cte("page")
        count = select(func.count().label("total")).select_from(filtered).cte("count")
        rows = (await self.session.execute(select(count.c.total, *page.c).select_from(
            count.outerjoin(page, true())).order_by(page.c.created_at.desc(), page.c.source, page.c.id.desc()))).mappings().all()
        return [dict(r) for r in rows if r["id"] is not None], rows[0]["total"]
