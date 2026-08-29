from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base.database_model import BaseRepository
from src.models.students.models import Students
from src.models.students.models_dto import CreateStudentDTO


class StudentRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=Students,
        )

    async def add_student(
        self,
        data: CreateStudentDTO,
    ) -> Students:
        """Добавление новой записи студента в сессию"""
        return self.add(data)

    async def get_student_by_id(self, student_id: int) -> Students | None:
        """Получение студента по ID"""
        return await self.get_by_id(Students, student_id)

    async def get_student_by_user_id(self, user_id: int) -> Students | None:
        """Получение профиля студента по user_id"""
        result_db = await self.session.execute(
            select(Students).where(Students.user_id == user_id)
        )
        return result_db.scalar_one_or_none()

    async def get_all_students(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Students]:
        """Получение списка всех студентов с пагинацией"""
        result_db = await self.session.execute(
            select(Students).limit(limit).offset(offset)
        )
        return list(result_db.scalars().all())

    async def update_student(
        self,
        student_id: int,
        values: dict,
    ) -> Students | None:
        """Обновление данных студента по ID"""
        result_db = await self.session.execute(
            update(Students)
            .where(Students.id == student_id)
            .values(**values)
            .returning(Students)
        )
        return result_db.scalar_one_or_none()

    async def update_student_by_user_id(
        self,
        user_id: int,
        values: dict,
    ) -> Students | None:
        """Обновление данных студента по user_id"""
        result_db = await self.session.execute(
            update(Students)
            .where(Students.user_id == user_id)
            .values(**values)
            .returning(Students)
        )
        return result_db.scalar_one_or_none()

    async def delete_student(self, student_id: int) -> Students | None:
        """Удаление студента по ID"""
        result_db = await self.session.execute(
            delete(Students)
            .where(Students.id == student_id)
            .returning(Students)
        )
        return result_db.scalar_one_or_none()

    async def delete_student_by_user_id(self, user_id: int) -> Students | None:
        """Удаление студента по user_id"""
        result_db = await self.session.execute(
            delete(Students)
            .where(Students.user_id == user_id)
            .returning(Students)
        )
        return result_db.scalar_one_or_none()
