from src.modules.check_permission.repository import material_scope
from src.modules.users.models import UserRole
from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy import select, delete, update, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.lectures.models import Lecture
from src.modules.lesson_students.models import LessonStudent
from src.modules.lectures.models_dto import CreateLectureRequestDTO


class LecturesRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=Lecture,
        )

    async def lock_recipient_and_count(self, recipient_id: int) -> int:
        await self.session.scalar(select(LessonStudent.id).where(LessonStudent.id == recipient_id).with_for_update())
        return await self.session.scalar(select(func.count()).select_from(Lecture).where(Lecture.lesson_student_id == recipient_id)) or 0

    async def add_lecture(
        self,
        data: CreateLectureRequestDTO,
    ) -> Lecture:
        return self.add(data)

    async def get_by_id(self, lecture_id: int) -> Lecture | None:
        return await super().get_by_id(Lecture, lecture_id)

    async def get_all_by_lesson_student_id(
        self,
        lesson_student_id: int,
        limit: int = 100,
        offset: int = 0,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sort_date: str = "desc",
        actor=None,
    ) -> Tuple[List[Lecture], int]:
        """Получает список лекций по ID связи занятие-ученик с фильтрацией, пагинацией и сортировкой.
        Использует оконную функцию для гарантированной синхронности данных и счетчика."""
        filters = [Lecture.lesson_student_id == lesson_student_id]
        if actor is not None:
            filters.append(material_scope(Lecture, actor.id, actor.role))
        if from_date:
            filters.append(Lecture.created_at >= from_date)
        if to_date:
            filters.append(Lecture.created_at <= to_date)

        conditions = and_(*filters) if filters else True

        count_stmt = select(func.count()).select_from(Lecture).where(conditions)
        total = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = select(Lecture).where(conditions)

        if sort_date.lower() == "asc":
            stmt = stmt.order_by(Lecture.created_at.asc(), Lecture.id.asc())
        else:
            stmt = stmt.order_by(Lecture.created_at.desc(), Lecture.id.desc())

        stmt = stmt.limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total
        
    async def get_all_by_student_id(
        self,
        student_id: int,
        limit: int = 100,
        offset: int = 0,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sort_date: str = "desc",
        actor=None,
        course_id: int | None = None,
        view=None,
    ) -> Tuple[List[Lecture], int]:
        """Получить все лекции студента по всем курсам (JOIN к lesson_students)"""
        filters = [LessonStudent.student_id == student_id]
        if actor is not None:
            filters.append(material_scope(Lecture, actor.id, actor.role))
        if from_date:
            filters.append(Lecture.created_at >= from_date)
        if to_date:
            filters.append(Lecture.created_at <= to_date)
            
        from src.modules.lessons.models import Lesson
        from src.modules.check_permission.repository import lesson_active_scope
        from src.modules.base.list_query import snapshot_page, view_scope, ListView
        if course_id is not None:
            filters.append(Lesson.course_id == course_id)
        if actor is not None:
            filters.append(view_scope(lesson_active_scope(actor.id, actor.role), view or ListView.ALL))
        stmt = select(Lecture).join(LessonStudent, Lecture.lesson_student_id == LessonStudent.id).join(
            Lesson, Lesson.id == LessonStudent.lesson_id).where(*filters)
        order = (lambda l: l.created_at.asc(), lambda l: l.id.asc()) if sort_date.lower() == 'asc' else (
            lambda l: l.created_at.desc(), lambda l: l.id.desc())
        return await snapshot_page(self.session, Lecture, stmt, order, limit, offset)

    async def update_lecture_paths(
        self,
        lecture_id: int,
        original_file_path: str,
        pdf_file_path: str,
    ) -> Lecture | None:
        """Обновляет пути к файлам для уже созданной записи лекции"""
        stmt = (
            update(Lecture)
            .where(Lecture.id == lecture_id)
            .values(
                original_file_path=original_file_path,
                pdf_file_path=pdf_file_path,
            )
            .returning(Lecture)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_lecture(self, lecture_id: int) -> Lecture | None:
        """Удаляет лекцию по ее ID"""
        stmt = delete(Lecture).where(Lecture.id == lecture_id).returning(Lecture)
        result = await self.session.execute(stmt)
        deleted = result.scalar_one_or_none()
        if deleted:
            from src.modules.files.repository import FileAssetsRepository
            await FileAssetsRepository(self.session).prune(
                {deleted.original_asset_id, deleted.download_asset_id} - {None})
        return deleted

    async def detail_visible(self, lecture_id: int, actor) -> Lecture | None:
        from src.modules.check_permission.repository import recipient_scope
        return await self.session.scalar(select(Lecture).join(LessonStudent).where(
            Lecture.id == lecture_id, recipient_scope(actor.id, actor.role), material_scope(Lecture, actor.id, actor.role)))
