from sqlalchemy import select, exists, tuple_
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.base.repository_model import BaseRepository
from src.modules.homeworks.models import Homework
from src.modules.users.models import User
from src.modules.homework_submissions.models import HomeworkSubmission, HomeworkSubmissionStatus
from src.modules.lessons.models import Lesson, LessonStatus
from src.modules.lesson_students.models import LessonStudent
from src.modules.check_permission.repository import material_scope, recipient_history_scope
from src.modules.homework_placements.models import HomeworkPlacement, HomeworkDeadlineEvent


class HomeworkPlacementsRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=HomeworkPlacement)

    async def homework(self, homework_id: int) -> Homework | None:
        return await self.session.scalar(select(Homework).where(Homework.id == homework_id)
            .with_for_update().execution_options(populate_existing=True))

    async def context(self, recipient_id: int) -> tuple[LessonStudent, Lesson]:
        recipient, lesson = (await self.session.execute(select(LessonStudent, Lesson).join(
            Lesson, Lesson.id == LessonStudent.lesson_id).where(LessonStudent.id == recipient_id))).one()
        return recipient, lesson

    async def placements(self, homework_id: int, actor: User | None = None) -> list[HomeworkPlacement]:
        stmt = select(HomeworkPlacement).where(HomeworkPlacement.homework_id == homework_id)
        if actor is not None:
            stmt = stmt.where(material_scope(HomeworkPlacement, actor.id, actor.role))
        return list((await self.session.scalars(stmt.order_by(HomeworkPlacement.id))).all())

    async def events(self, placement_id: int, actor: User | None = None) -> list[HomeworkDeadlineEvent]:
        stmt = select(HomeworkDeadlineEvent).where(HomeworkDeadlineEvent.placement_id == placement_id)
        if actor is not None:
            stmt = stmt.where(material_scope(HomeworkDeadlineEvent, actor.id, actor.role))
        return list((await self.session.scalars(stmt.order_by(HomeworkDeadlineEvent.id))).all())

    async def candidate(self, recipient: LessonStudent, lesson: Lesson) -> Lesson | None:
        return await self.session.scalar(select(Lesson).join(LessonStudent, LessonStudent.lesson_id == Lesson.id).where(
            Lesson.course_id == lesson.course_id, LessonStudent.student_id == recipient.student_id,
            LessonStudent.access_ended_at.is_(None), Lesson.is_deleted.is_(False),
            Lesson.status != LessonStatus.CANCELLED, recipient_history_scope(),
            tuple_(Lesson.scheduled_at, Lesson.id) > tuple_(lesson.scheduled_at, lesson.id),
        ).order_by(Lesson.scheduled_at, Lesson.id).limit(1))

    async def course_homeworks(self, course_id: int) -> list[Homework]:
        return list((await self.session.scalars(select(Homework).join(
            LessonStudent, LessonStudent.id == Homework.lesson_student_id).join(
            Lesson, Lesson.id == LessonStudent.lesson_id).where(Lesson.course_id == course_id)
            .order_by(Homework.id).with_for_update(of=Homework).execution_options(populate_existing=True))).all())

    async def checked(self, homework_id: int) -> bool:
        return bool(await self.session.scalar(select(exists().where(
            HomeworkSubmission.homework_id == homework_id, HomeworkSubmission.is_working.is_(True),
            HomeworkSubmission.status == HomeworkSubmissionStatus.CHECKED))))

    async def lesson_homeworks(self, recipient_id: int, actor: User) -> list[Homework]:
        return list((await self.session.scalars(select(Homework).join(
            HomeworkPlacement, HomeworkPlacement.homework_id == Homework.id).where(
                HomeworkPlacement.lesson_student_id == recipient_id,
                material_scope(Homework, actor.id, actor.role),
                material_scope(HomeworkPlacement, actor.id, actor.role)).order_by(Homework.id))).all())

    async def working_status(self, homework_id: int, actor: User) -> str | None:
        from src.modules.check_permission.repository import submission_scope
        return await self.session.scalar(select(HomeworkSubmission.status).where(
            HomeworkSubmission.homework_id == homework_id, HomeworkSubmission.is_working.is_(True),
            submission_scope(HomeworkSubmission, actor.id, actor.role)))

    async def course_active(self, course_id: int) -> bool:
        from src.modules.courses.models import Course
        return bool(await self.session.scalar(select(Course.id).where(
            Course.id == course_id, Course.is_deleted.is_(False))))
