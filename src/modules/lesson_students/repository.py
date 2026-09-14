from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.modules.base.database_model import BaseRepository
from src.modules.lesson_students.models import LessonStudent


class LessonStudentsRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=LessonStudent,
        )

    async def add_student_to_lesson(
        self,
        data: BaseModel,
    ) -> LessonStudent:
        """Добавляет студента на урок"""
        return self.add(data)

    async def get_by_lesson_and_student(
        self,
        lesson_id: int,
        student_id: int,
    ) -> LessonStudent | None:
        """Получает запись о прикреплении, если она существует"""
        stmt = select(LessonStudent).where(
            LessonStudent.lesson_id == lesson_id,
            LessonStudent.student_id == student_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def remove_student_from_lesson(
        self,
        lesson_id: int,
        student_id: int,
    ) -> LessonStudent:
        """Удаляет студента с урока (возвращает удаленную запись)"""
        stmt = select(LessonStudent).where(
            LessonStudent.lesson_id == lesson_id,
            LessonStudent.student_id == student_id,
        )
        result = await self.session.execute(stmt)
        lesson_student = result.scalar_one()

        await self.session.delete(lesson_student)
        return lesson_student
