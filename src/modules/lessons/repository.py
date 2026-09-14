from typing import Tuple, List, Optional
from datetime import datetime
from sqlalchemy import update, delete, select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import BaseRepository
from src.modules.lessons.models import Lesson
from src.modules.lesson_students.models import LessonStudent
from src.modules.lessons.models_dto import CreateLessonDTO


class LessonsRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=Lesson,
        )

    async def add_lesson(
        self,
        data: CreateLessonDTO,
    ) -> Lesson:
        """Добавляет запись занятия"""
        return self.add(data)

    async def get_lesson_by_id(self, lesson_id: int) -> Lesson | None:
        """Находит занятие по ID"""
        return await self.get_by_id(Lesson, lesson_id)

    async def get_lessons(
        self,
        limit: int = 100,
        offset: int = 0,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        course_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        student_id: Optional[int] = None,
    ) -> Tuple[List[Lesson], int]:
        """Получает список занятий с фильтрацией, пагинацией и сортировкой"""
        stmt = select(Lesson)
        count_stmt = select(func.count()).select_from(Lesson)

        # Фильтры
        conditions = []
        if from_date:
            conditions.append(Lesson.scheduled_at >= from_date)
        if to_date:
            conditions.append(Lesson.scheduled_at <= to_date)
        if course_id:
            conditions.append(Lesson.course_id == course_id)
        if teacher_id:
            conditions.append(Lesson.teacher_id == teacher_id)
        if student_id:
            # Если это студент, он должен быть привязан к занятию через lesson_students
            stmt = stmt.join(LessonStudent, Lesson.id == LessonStudent.lesson_id)
            count_stmt = count_stmt.join(LessonStudent, Lesson.id == LessonStudent.lesson_id)
            conditions.append(LessonStudent.student_id == student_id)

        if conditions:
            stmt = stmt.where(*conditions)
            count_stmt = count_stmt.where(*conditions)

        # Подгружаем зависимости для определения наличия лекций/дз
        stmt = stmt.options(
            selectinload(Lesson.lesson_students).selectinload(LessonStudent.lectures),
            selectinload(Lesson.lesson_students).selectinload(LessonStudent.homeworks)
        )

        # Сортировка по дате по убыванию, затем лимит и оффсет
        stmt = stmt.order_by(Lesson.scheduled_at.desc()).limit(limit).offset(offset)

        # Выполняем подсчет общего количества
        total_count = await self.session.execute(count_stmt)
        total_count = total_count.scalar() or 0

        # Получаем сами занятия
        result = await self.session.execute(stmt)
        items = list(result.scalars().all())

        return items, total_count

    async def update_lesson(
        self,
        lesson_id: int,
        values: dict,
    ) -> Lesson | None:
        """Обновляет значения занятия по ID"""
        result_db = await self.session.execute(
            update(Lesson)
            .where(Lesson.id == lesson_id)
            .values(**values)
            .returning(Lesson)
        )
        return result_db.scalar_one_or_none()

    async def delete_lesson(self, lesson_id: int) -> Lesson | None:
        """Удаляет занятие по ID"""
        result_db = await self.session.execute(
            delete(Lesson)
            .where(Lesson.id == lesson_id)
            .returning(Lesson)
        )
        return result_db.scalar_one_or_none()
