from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base.database_model import BaseRepository
from src.models.teachers.models import Teachers
from src.models.teachers.models_dto import CreateTeacherDTO


class TeacherRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=Teachers,
        )

    async def add_teacher(
        self,
        data: CreateTeacherDTO,
    ) -> Teachers:
        """Добавление новой записи преподавателя в сессию"""
        return self.add(data)

    async def get_teacher_by_id(self, teacher_id: int) -> Teachers | None:
        """Получение преподавателя по ID"""
        return await self.get_by_id(Teachers, teacher_id)

    async def get_teacher_by_user_id(self, user_id: int) -> Teachers | None:
        """Получение профиля преподавателя по user_id"""
        result_db = await self.session.execute(
            select(Teachers).where(Teachers.user_id == user_id)
        )
        return result_db.scalar_one_or_none()

    async def get_all_teachers(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Teachers]:
        """Получение списка всех преподавателей с пагинацией"""
        result_db = await self.session.execute(
            select(Teachers).limit(limit).offset(offset)
        )
        return list(result_db.scalars().all())

    async def update_teacher(
        self,
        teacher_id: int,
        values: dict,
    ) -> Teachers | None:
        """Обновление данных преподавателя по ID"""
        result_db = await self.session.execute(
            update(Teachers)
            .where(Teachers.id == teacher_id)
            .values(**values)
            .returning(Teachers)
        )
        return result_db.scalar_one_or_none()

    async def update_teacher_by_user_id(
        self,
        user_id: int,
        values: dict,
    ) -> Teachers | None:
        """Обновление данных преподавателя по user_id"""
        result_db = await self.session.execute(
            update(Teachers)
            .where(Teachers.user_id == user_id)
            .values(**values)
            .returning(Teachers)
        )
        return result_db.scalar_one_or_none()

    async def delete_teacher(self, teacher_id: int) -> Teachers | None:
        """Удаление преподавателя по ID"""
        result_db = await self.session.execute(
            delete(Teachers)
            .where(Teachers.id == teacher_id)
            .returning(Teachers)
        )
        return result_db.scalar_one_or_none()

    async def delete_teacher_by_user_id(self, user_id: int) -> Teachers | None:
        """Удаление преподавателя по user_id"""
        result_db = await self.session.execute(
            delete(Teachers)
            .where(Teachers.user_id == user_id)
            .returning(Teachers)
        )
        return result_db.scalar_one_or_none()
