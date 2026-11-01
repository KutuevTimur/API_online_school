"""Read-only capabilities derived from domain state and the authenticated role."""
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.check_permission.repository import ReadContextRepository
from src.modules.users.models import User, UserRole


def recipient_reason(row: dict) -> str | None:
    if row['course_archived']:
        return 'course_archived'
    if row['lesson_archived']:
        return 'lesson_archived'
    if row['link_ended'] is not None:
        return 'teacher_link_ended'
    if not row['enrollment_id'] or row['history_revoked']:
        return 'history_only'
    if row['enrollment_deleted'] or row['enrollment_ended'] is not None:
        return 'enrollment_ended'
    if row['expires_at'] is not None and row['expires_at'] <= row['now']:
        return 'access_expired'
    if row['recipient_ended'] is not None or row['started_at'] > row['now']:
        return 'history_only'
    return None


def access(reason: str | None, actor: User) -> dict:
    return dict(access_mode='read_only' if reason else 'active', read_only_reason=reason,
                can_manage=reason is None and actor.role == UserRole.TEACHER)


class ReadContextService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = ReadContextRepository(session)

    async def courses(self, dtos: list, actor: User) -> list:
        states = {r.id: r for r in await self.repo.course_states(actor, [d.id for d in dtos])}
        memberships = {r[0]: r for r in await self.repo.course_student_states(actor, list(states))} if actor.role == UserRole.STUDENT else {}
        creatable = await self.repo.creatable_courses(list(states))
        for dto in dtos:
            state = states[dto.id]
            reason = 'course_archived' if state.is_deleted else None
            if reason is None and not state.active:
                row = memberships.get(dto.id)
                reason = ('teacher_link_ended' if row and row[6] is not None else
                    'enrollment_ended' if row and (row[1] or row[3] is not None) else
                    'access_expired' if row and row[4] is not None and row[4] <= row[7] else 'history_only')
            for key, value in access(reason, actor).items():
                setattr(dto, key, value)
            dto.can_create_lesson = dto.can_manage and dto.id in creatable
        return dtos

    async def lessons(self, dtos: list, actor: User) -> list:
        rows = await self.repo.recipients(await self.repo.lesson_recipients(actor, [d.id for d in dtos]))
        states = await self.repo.lesson_states([d.id for d in dtos])
        for dto in dtos:
            recipients = [r for r in rows.values() if r['lesson_id'] == dto.id]
            reason = next((recipient_reason(r) for r in recipients if recipient_reason(r)), None)
            if not recipients or states[dto.id].recipients > 1:
                reason = reason or 'history_only'
            if states[dto.id].course_archived:
                reason = 'course_archived'
            elif dto.is_deleted:
                reason = 'lesson_archived'
            for key, value in access(reason, actor).items():
                setattr(dto, key, value)
        return dtos
