from src.modules.check_permission.repository import material_scope
from src.modules.users.models import User
from src.modules.base.list_query import ListView
from src.modules.homeworks.models_dto import HomeworkListStatus
from typing import Any, List
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from src.modules.base.repository_model import BaseRepository
from src.modules.homeworks.models import Homework
from src.modules.lesson_students.models import LessonStudent
from src.modules.homeworks.models_dto import CreateHomeworkRequestDTO


class HomeworksRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=Homework,
        )

    async def add_homework(
        self,
        data: CreateHomeworkRequestDTO,
    ) -> Homework:
        return self.add(data)

    async def get_by_id(self, homework_id: int) -> Homework | None:
        return await super().get_by_id(Homework, homework_id)

    async def get_all_by_lesson_student_id(self, lesson_student_id: int, actor=None) -> List[Homework]:
        stmt = select(Homework).where(Homework.lesson_student_id == lesson_student_id)
        if actor is not None:
            stmt = stmt.where(material_scope(Homework, actor.id, actor.role))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
        
    async def get_all_by_student_id(self, student_id: int, actor=None) -> List[Homework]:
        """Получить все домашние задания студента по всем урокам / курсам (JOIN к lesson_students)"""
        stmt = select(Homework).join(
            LessonStudent, Homework.lesson_student_id == LessonStudent.id
        ).where(LessonStudent.student_id == student_id)
        if actor is not None:
            stmt = stmt.where(material_scope(Homework, actor.id, actor.role))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_homework_paths(
        self,
        homework_id: int,
        original_file_path: str,
        pdf_file_path: str,
    ) -> Homework | None:
        """Обновляет пути к файлам для уже созданной записи ДЗ"""
        stmt = (
            update(Homework)
            .where(Homework.id == homework_id)
            .values(
                original_file_path=original_file_path,
                pdf_file_path=pdf_file_path,
            )
            .returning(Homework)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def has_submissions(self, homework_id: int) -> bool:
        from sqlalchemy import exists
        from src.modules.homework_submissions.models import HomeworkSubmission
        return bool(await self.session.scalar(select(exists().where(
            HomeworkSubmission.homework_id == homework_id))))

    async def delete_homework(self, homework_id: int) -> Homework | None:
        stmt = delete(Homework).where(Homework.id == homework_id).returning(Homework)
        result = await self.session.execute(stmt)
        deleted = result.scalar_one_or_none()
        if deleted:
            from src.modules.files.repository import FileAssetsRepository
            await FileAssetsRepository(self.session).prune(
                {deleted.original_asset_id, deleted.download_asset_id} - {None})
        return deleted

    async def student_page(self, actor: User, limit: int, offset: int, course_id: int | None,
                           status: HomeworkListStatus, view: ListView, overdue_only: bool) -> tuple[list[Homework], int]:
        from sqlalchemy import func, or_
        from src.modules.base.list_query import snapshot_page, view_scope
        from src.modules.check_permission.repository import submission_scope, lesson_active_scope
        from src.modules.homework_submissions.models import HomeworkSubmission
        from src.modules.homework_placements.models import HomeworkPlacement, HomeworkDeadlineEvent
        from src.modules.lessons.models import Lesson

        # Pick the last visible placement BEFORE applying view/course filters.
        latest = (select(HomeworkPlacement.id).where(
            HomeworkPlacement.homework_id == Homework.id,
            material_scope(HomeworkPlacement, actor.id, actor.role))
            .order_by(HomeworkPlacement.id.desc()).limit(1).correlate(Homework).scalar_subquery())
        working = (select(HomeworkSubmission.status).where(
            HomeworkSubmission.homework_id == Homework.id, HomeworkSubmission.is_working.is_(True),
            submission_scope(HomeworkSubmission, actor.id, actor.role))
            .correlate(Homework).scalar_subquery())
        # Match the response's last visible deadline journal event, including NULL.
        deadline = (select(HomeworkDeadlineEvent.due_at).where(
            HomeworkDeadlineEvent.placement_id == HomeworkPlacement.id,
            material_scope(HomeworkDeadlineEvent, actor.id, actor.role))
            .order_by(HomeworkDeadlineEvent.id.desc()).limit(1)
            .correlate(HomeworkPlacement).scalar_subquery())
        stmt = (select(Homework).join(HomeworkPlacement, HomeworkPlacement.id == latest)
            .join(LessonStudent, LessonStudent.id == HomeworkPlacement.lesson_student_id)
            .join(Lesson, Lesson.id == LessonStudent.lesson_id)
            .where(material_scope(Homework, actor.id, actor.role),
                   view_scope(lesson_active_scope(actor.id, actor.role), view)))
        if course_id is not None:
            stmt = stmt.where(Lesson.course_id == course_id)
        if status == HomeworkListStatus.TODO:
            stmt = stmt.where(or_(working.is_(None), working == "draft"))
        elif status != HomeworkListStatus.ALL:
            stmt = stmt.where(working == status.value)
        if overdue_only:
            stmt = stmt.where(deadline < func.statement_timestamp(), or_(working.is_(None), working != "checked"))
        def checked_order(homework: Any) -> ColumnElement:
            return (select(HomeworkSubmission.checked_at).where(
                HomeworkSubmission.homework_id == homework.id,
                HomeworkSubmission.is_working.is_(True),
                submission_scope(HomeworkSubmission, actor.id, actor.role))
                .correlate(homework).scalar_subquery().desc().nulls_last())

        ordering = ((checked_order, lambda h: h.id.desc()) if status == HomeworkListStatus.CHECKED
                    else (lambda h: h.created_at.desc(), lambda h: h.id.desc()))
        return await snapshot_page(self.session, Homework, stmt, ordering, limit, offset)

    async def read_batch(self, ids: list[int], actor):
        from src.modules.homework_placements.models import HomeworkPlacement, HomeworkDeadlineEvent
        from src.modules.homework_submissions.models import HomeworkSubmission
        from src.modules.check_permission.repository import submission_scope
        placements = list((await self.session.scalars(select(HomeworkPlacement).where(
            HomeworkPlacement.homework_id.in_(ids), material_scope(HomeworkPlacement, actor.id, actor.role))
            .order_by(HomeworkPlacement.id))).all())
        events = list((await self.session.scalars(select(HomeworkDeadlineEvent).where(
            HomeworkDeadlineEvent.placement_id.in_([p.id for p in placements]),
            material_scope(HomeworkDeadlineEvent, actor.id, actor.role)).order_by(HomeworkDeadlineEvent.id))).all())
        working = (await self.session.execute(select(HomeworkSubmission.homework_id,
            HomeworkSubmission.id, HomeworkSubmission.status).where(HomeworkSubmission.homework_id.in_(ids),
            HomeworkSubmission.is_working.is_(True), submission_scope(HomeworkSubmission, actor.id, actor.role)))).all()
        answered = set((await self.session.scalars(select(HomeworkSubmission.homework_id).where(
            HomeworkSubmission.homework_id.in_(ids)))).all())
        return placements, {e.placement_id: e for e in events}, {r.homework_id: r for r in working}, answered

    async def available_debts(self, actor, target, limit: int, offset: int):
        from sqlalchemy import exists, tuple_, func, or_
        from src.modules.base.list_query import snapshot_page
        from src.modules.homework_submissions.models import HomeworkSubmission
        from src.modules.homework_placements.models import HomeworkPlacement
        from src.modules.lessons.models import Lesson
        from src.modules.check_permission.repository import recipient_scope
        latest_lesson = (select(HomeworkPlacement.id).where(HomeworkPlacement.homework_id == Homework.id)
            .order_by(HomeworkPlacement.id.desc()).limit(1).correlate(Homework).scalar_subquery())
        from sqlalchemy.orm import aliased
        latest_p = aliased(HomeworkPlacement)
        latest_r = aliased(LessonStudent)
        latest_l = aliased(Lesson)
        earlier = exists(select(latest_p.id).join(latest_r, latest_r.id == latest_p.lesson_student_id)
            .join(latest_l, latest_l.id == latest_r.lesson_id).where(latest_p.id == latest_lesson,
                tuple_(latest_l.scheduled_at, latest_l.id) < tuple_(target.scheduled_at, target.id)).correlate(Homework))
        added = exists(select(HomeworkPlacement.id).where(HomeworkPlacement.homework_id == Homework.id,
            HomeworkPlacement.lesson_student_id == target.recipient_id).correlate(Homework))
        stmt = (select(Homework).join(LessonStudent, LessonStudent.id == Homework.lesson_student_id)
            .join(Lesson, Lesson.id == LessonStudent.lesson_id).where(
                Lesson.course_id == target.course_id, LessonStudent.student_id == target.student_id,
                tuple_(Lesson.scheduled_at, Lesson.id) < tuple_(target.scheduled_at, target.id),
                recipient_scope(actor.id, actor.role), material_scope(Homework, actor.id, actor.role),
                Homework.deadline_frozen_at.is_(None), or_(earlier, added),
                ~exists(select(HomeworkSubmission.id).where(HomeworkSubmission.homework_id == Homework.id,
                    HomeworkSubmission.is_working.is_(True), HomeworkSubmission.status == 'checked').correlate(Homework))))
        return await snapshot_page(self.session, Homework, stmt,
            (lambda h: h.created_at.desc(), lambda h: h.id.desc()), limit, offset)
