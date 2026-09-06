from typing import List, Optional

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import BaseRepository
from src.modules.teachers.models import Teacher
from src.modules.teachers.models_dto import CreateTeacherDTO


class TeacherRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=Teacher,
        )

    async def add_teacher(
        self,
        data: CreateTeacherDTO,
    ) -> Teacher:
        """Добавление новой записи преподавателя в сессию"""
        return self.add(data)

    async def get_teacher_by_id(self, teacher_id: int) -> Teacher | None:
        """Получение преподавателя по ID"""
        return await self.get_by_id(Teacher, teacher_id)

    async def get_teacher_by_user_id(self, user_id: int) -> Teacher | None:
        """Получение профиля преподавателя по user_id"""
        result_db = await self.session.execute(
            select(Teacher).where(Teacher.user_id == user_id)
        )
        return result_db.scalar_one_or_none()

    async def get_all_teachers(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Teacher]:
        """Получение списка всех преподавателей с пагинацией"""
        result_db = await self.session.execute(
            select(Teacher).limit(limit).offset(offset)
        )
        return list(result_db.scalars().all())

    async def update_teacher(
        self,
        teacher_id: int,
        values: dict,
    ) -> Teacher | None:
        """Обновление данных преподавателя по ID"""
        result_db = await self.session.execute(
            update(Teacher)
            .where(Teacher.id == teacher_id)
            .values(**values)
            .returning(Teacher)
        )
        return result_db.scalar_one_or_none()

    async def update_teacher_by_user_id(
        self,
        user_id: int,
        values: dict,
    ) -> Teacher | None:
        """Обновление данных преподавателя по user_id"""
        result_db = await self.session.execute(
            update(Teacher)
            .where(Teacher.user_id == user_id)
            .values(**values)
            .returning(Teacher)
        )
        return result_db.scalar_one_or_none()

    async def delete_teacher(self, teacher_id: int) -> Teacher | None:
        """Удаление преподавателя по ID"""
        result_db = await self.session.execute(
            delete(Teacher)
            .where(Teacher.id == teacher_id)
            .returning(Teacher)
        )
        return result_db.scalar_one_or_none()

    async def delete_teacher_by_user_id(self, user_id: int) -> Teacher | None:
        """Удаление преподавателя по user_id"""
        result_db = await self.session.execute(
            delete(Teacher)
            .where(Teacher.user_id == user_id)
            .returning(Teacher)
        )
        return result_db.scalar_one_or_none()
