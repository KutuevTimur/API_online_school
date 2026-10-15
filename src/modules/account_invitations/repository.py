from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.base.repository_model import BaseRepository
from src.modules.account_invitations.models import AccountInvitation, AccountAudit
from src.modules.teacher_students.models import TeacherStudent
from src.modules.teachers.models import Teacher
from src.modules.students.models import Student


class InvitationRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=AccountInvitation)

    async def find(self, digest: str, lock: bool = False) -> AccountInvitation | None:
        stmt = select(AccountInvitation).where(AccountInvitation.digest == digest)
        if lock:
            stmt = stmt.with_for_update().execution_options(populate_existing=True)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def invalidate(self, user_id: int, purpose: str) -> None:
        await self.session.execute(update(AccountInvitation).where(
            AccountInvitation.user_id == user_id, AccountInvitation.purpose == purpose
        ).values(consumed=True))

    async def insert(self, **values) -> None:
        self.session.add(AccountInvitation(**values))

    async def audit(self, **values) -> None:
        self.session.add(AccountAudit(**values))

    async def is_linked(self, teacher_user_id: int, student_user_id: int) -> bool:
        stmt = select(TeacherStudent.id).join(Teacher, Teacher.id == TeacherStudent.teacher_id).join(
            Student, Student.id == TeacherStudent.student_id).where(
            Teacher.user_id == teacher_user_id, Student.user_id == student_user_id,
            TeacherStudent.ended_at.is_(None))
        return (await self.session.execute(stmt)).first() is not None


class RateLimitRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        from src.modules.account_invitations.models import AuthRateLimit
        super().__init__(session=session, model=AuthRateLimit)

    async def cleanup(self, window: int) -> None:
        from sqlalchemy import delete
        await self.session.execute(delete(self.model).where(self.model.window < window - 1))

    async def increment(self, key: str, window: int) -> int:
        from sqlalchemy import case
        from sqlalchemy.dialects.postgresql import insert
        model = self.model
        stmt = insert(model).values(key=key, window=window, count=1)
        stmt = stmt.on_conflict_do_update(index_elements=[model.key], set_={
            "window": window, "count": case((model.window == window, model.count + 1), else_=1)
        }).returning(model.count)
        return (await self.session.execute(stmt)).scalar_one()
