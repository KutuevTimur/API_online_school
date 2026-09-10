from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import BaseRepository
from src.modules.lesson_students.models import LessonStudent
from src.modules.lesson_students.models_dto import CreateLessonStudentRequestDTO


class LessonStudentsRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=LessonStudent,
        )

    async def add_student_to_lesson(
        self,
        data: CreateLessonStudentRequestDTO,
    ) -> LessonStudent:
        """Добавляет студента на занятие"""
        return self.add(data)

    async def get_by_lesson_and_student(
        self,
        lesson_id: int,
        student_id: int,
    ) -> LessonStudent | None:
        """Получает запись привязки по lesson_id и student_id"""
        stmt = select(LessonStudent).where(
            LessonStudent.lesson_id == lesson_id,
            LessonStudent.student_id == student_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_lesson_students(self, lesson_student_id: int) -> LessonStudent | None:
        return await super().get_by_id(LessonStudent, lesson_student_id)

    async def delete_student_from_lesson(
        self,
        lesson_id: int,
        student_id: int,
    ) -> LessonStudent | None:
        """Удаляет студента с занятия"""
        stmt = (
            delete(LessonStudent)
            .where(
                LessonStudent.lesson_id == lesson_id,
                LessonStudent.student_id == student_id
            )
            .returning(LessonStudent)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
