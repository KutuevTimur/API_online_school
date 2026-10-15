from datetime import datetime, UTC
from sqlalchemy import select, func, update, true
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.base.repository_model import BaseRepository
from src.modules.notifications.models import Notification
from src.modules.students.models import Student
from src.modules.teachers.models import Teacher
from src.modules.lessons.models import Lesson
from src.modules.lesson_students.models import LessonStudent
from src.modules.homeworks.models import Homework


class NotificationsRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Notification)

    async def stage(self, recipient: int, event: str, kind: str, target: int, key: str) -> None:
        await self.session.execute(insert(Notification).values(recipient_user_id=recipient,
            event_type=event, object_type=kind, object_id=target, dedupe_key=key)
            .on_conflict_do_nothing(constraint="uq_notification_recipient_event"))

    async def page(self, user_id: int, limit: int, offset: int, unread_only: bool) -> tuple[list[Notification], int]:
        scope = [Notification.recipient_user_id == user_id]
        if unread_only:
            scope.append(Notification.read_at.is_(None))
        # One statement gives rows and count the same PostgreSQL snapshot, even on an empty page.
        filtered = select(Notification).where(*scope).cte("filtered")
        page = select(filtered).order_by(filtered.c.created_at.desc(), filtered.c.id.desc()).limit(limit).offset(offset).cte("page")
        count = select(func.count().label("total")).select_from(filtered).cte("count")
        rows = (await self.session.execute(select(count.c.total, *page.c).select_from(
            count.outerjoin(page, true())).order_by(page.c.created_at.desc(), page.c.id.desc()))).mappings().all()
        return [Notification(**{c.name: r[c.name] for c in Notification.__table__.columns})
                for r in rows if r["id"] is not None], rows[0]["total"]

    async def unread(self, user_id: int) -> int:
        return await self.session.scalar(select(func.count()).select_from(Notification).where(
            Notification.recipient_user_id == user_id, Notification.read_at.is_(None)))

    async def owned(self, user_id: int, notification_id: int) -> Notification | None:
        return await self.session.scalar(select(Notification).where(
            Notification.id == notification_id, Notification.recipient_user_id == user_id))

    async def mark_read(self, user_id: int, notification_id: int) -> Notification | None:
        return (await self.session.execute(update(Notification).where(Notification.id == notification_id,
            Notification.recipient_user_id == user_id).values(read_at=func.coalesce(
                Notification.read_at, datetime.now(UTC))).returning(Notification))).scalar_one_or_none()

    async def lesson_students(self, lesson_id: int) -> list[int]:
        return list((await self.session.scalars(select(Student.user_id).join(LessonStudent,
            LessonStudent.student_id == Student.id).where(LessonStudent.lesson_id == lesson_id,
            LessonStudent.access_ended_at.is_(None)))).all())

    async def homework_parties(self, homework_id: int) -> tuple[int, int]:
        return (await self.session.execute(select(Student.user_id, Teacher.user_id)
            .select_from(Homework).join(LessonStudent, Homework.lesson_student_id == LessonStudent.id)
            .join(Student, LessonStudent.student_id == Student.id)
            .join(Lesson, LessonStudent.lesson_id == Lesson.id)
            .join(Teacher, Lesson.teacher_id == Teacher.id).where(Homework.id == homework_id))).one()

    async def lesson_event_version(self, lesson_id: int) -> str:
        timestamp = await self.session.scalar(select(Lesson.updated_at).where(Lesson.id == lesson_id))
        return timestamp.isoformat()
