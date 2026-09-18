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
        """Добавляет новое занятие"""
        return self.add(data)

    async def get_lesson_by_id(self, lesson_id: int) -> Lesson | None:
        """Получает урок по ID (с жадной загрузкой связей для формирования флагов)"""
        stmt = (
            select(Lesson)
            .where(Lesson.id == lesson_id)
            .options(
                selectinload(Lesson.lesson_students).selectinload(LessonStudent.lectures),
                selectinload(Lesson.lesson_students).selectinload(LessonStudent.homeworks)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_lessons(
        self,
        limit: int = 100,
        offset: int = 0,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        course_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        student_id: Optional[int] = None,
        sort_date: str = "desc",
    ) -> Tuple[List[Lesson], int]:
        """Получает список уроков с фильтрацией, пагинацией и сортировкой.
        Использует оконную функцию для гарантированной синхронности данных и счетчика."""
        count_over = func.count().over().label('total_count')
        stmt = select(Lesson, count_over)

        # Base filters
        if from_date:
            stmt = stmt.where(Lesson.scheduled_at >= from_date)
        if to_date:
            stmt = stmt.where(Lesson.scheduled_at <= to_date)
        if course_id:
            stmt = stmt.where(Lesson.course_id == course_id)
        if teacher_id:
            stmt = stmt.where(Lesson.teacher_id == teacher_id)
            
        if student_id:
            stmt = stmt.join(Lesson.lesson_students).where(LessonStudent.student_id == student_id)

        # Pagination & Ordering
        if sort_date.lower() == "asc":
            stmt = stmt.order_by(Lesson.scheduled_at.asc())
        else:
            stmt = stmt.order_by(Lesson.scheduled_at.desc())
            
        stmt = stmt.limit(limit).offset(offset)
        
        stmt = stmt.options(
            selectinload(Lesson.lesson_students).selectinload(LessonStudent.lectures),
            selectinload(Lesson.lesson_students).selectinload(LessonStudent.homeworks)
        )

        result = await self.session.execute(stmt)
        rows = result.all()
        
        if not rows:
            return [], 0
            
        total = rows[0][1]
        lessons = [row[0] for row in rows]

        return lessons, total

    async def update_lesson(self, lesson_id: int, values: dict) -> Lesson:
        """Обновляет поля у урока"""
        stmt = (
            update(Lesson)
            .where(Lesson.id == lesson_id)
            .values(**values)
            .returning(Lesson)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete_lesson(self, lesson_id: int) -> Lesson:
        """Удаляет урок, возвращая удаленный объект"""
        stmt = (
            delete(Lesson)
            .where(Lesson.id == lesson_id)
            .returning(Lesson)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
