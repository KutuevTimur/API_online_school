"""SQL and deterministic mutexes; no commits or domain decisions."""
import hashlib
from typing import Any
from uuid import UUID
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.base.repository_model import BaseRepository
from src.modules.integrations_vk.models import ExternalContact


class IdentityRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=ExternalContact)

    async def mutex(self, namespace: int, key: str) -> None:
        digest = int.from_bytes(hashlib.sha256(key.encode()).digest()[:4], 'big', signed=True)
        await self.session.execute(text('SELECT pg_advisory_xact_lock(:ns, :key)'),
                                   {'ns': namespace, 'key': digest})

    async def schedules(self, user_ids: list[int]) -> None:
        for user_id in sorted(set(user_ids)):
            await self.session.execute(text('SELECT pg_advisory_xact_lock(80408, :id)'), {'id': user_id})

    async def rows(self, model: Any, *predicates: Any, lock: bool = False) -> list:
        stmt = select(model).where(*predicates).order_by(model.id)
        if lock:
            stmt = stmt.with_for_update(of=model).execution_options(populate_existing=True)
        return list((await self.session.scalars(stmt)).unique().all())

    async def one(self, model: Any, *predicates: Any, lock: bool = False) -> Any:
        rows = await self.rows(model, *predicates, lock=lock)
        return rows[0] if rows else None

    async def scoped(self, model: Any, connection: UUID, id: UUID, lock: bool = False) -> Any:
        return await self.one(model, model.connection_id == connection, model.id == id, lock=lock)

    async def teachers(self, connection: UUID) -> list[int]:
        from src.modules.integrations_vk.models import ConnectionTeacher
        return list((await self.session.scalars(select(ConnectionTeacher.teacher_user_id).where(
            ConnectionTeacher.connection_id == connection).order_by(ConnectionTeacher.teacher_user_id))).all())

    async def recipient_teachers(self, recipient: UUID) -> list[int]:
        from src.modules.integrations_vk.models import RecipientTeacher
        return list((await self.session.scalars(select(RecipientTeacher.teacher_user_id).where(
            RecipientTeacher.recipient_id == recipient).order_by(RecipientTeacher.teacher_user_id))).all())

    async def add_recipient_teacher(self, connection: UUID, recipient: UUID, teacher: int) -> None:
        from sqlalchemy.dialects.postgresql import insert
        from src.modules.integrations_vk.models import RecipientTeacher
        await self.session.execute(insert(RecipientTeacher).values(connection_id=connection,
            recipient_id=recipient, teacher_user_id=teacher).on_conflict_do_nothing())

    def stage(self, model: Any, **values: Any) -> Any:
        row = model(**values)
        self.session.add(row)
        return row

    async def workspace_candidates(self, teacher_id: int, student_id: int, *, eligible: bool) -> list:
        from sqlalchemy import exists, func
        from sqlalchemy.orm import aliased
        from src.modules.courses.models import Course
        from src.modules.student_courses.models import StudentCourse
        other = aliased(StudentCourse)
        stmt = select(Course).join(StudentCourse).where(
            Course.teacher_id == teacher_id, StudentCourse.student_id == student_id,
            ~exists(select(other.id).where(other.course_id == Course.id,
                other.student_id != student_id, other.is_deleted.is_(False),
                other.access_ended_at.is_(None),
                (other.expires_at.is_(None)) | (other.expires_at > func.clock_timestamp()))))
        if eligible:
            stmt = stmt.where(Course.is_deleted.is_(False), StudentCourse.is_deleted.is_(False),
                StudentCourse.access_ended_at.is_(None), StudentCourse.history_revoked.is_(False),
                StudentCourse.started_at <= func.clock_timestamp(),
                (StudentCourse.expires_at.is_(None)) | (StudentCourse.expires_at > func.clock_timestamp()))
        return list((await self.session.scalars(stmt.order_by(Course.id))).unique().all())


    async def planning_connections(self, actor_id: int) -> list:
        from src.modules.integrations_vk.models import IntegrationConnection, ConnectionTeacher
        return list((await self.session.scalars(select(IntegrationConnection).join(
            ConnectionTeacher, ConnectionTeacher.connection_id == IntegrationConnection.id).where(
            ConnectionTeacher.teacher_user_id == actor_id).order_by(IntegrationConnection.id))).all())
