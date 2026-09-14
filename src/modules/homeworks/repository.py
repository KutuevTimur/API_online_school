from typing import List
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import BaseRepository
from src.modules.homeworks.models import Homework
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
        """Добавляет запись домашнего задания"""
        return self.add(data)

    async def get_by_id(self, homework_id: int) -> Homework | None:
        """Получает ДЗ по ее ID"""
        return await super().get_by_id(Homework, homework_id)

    async def get_all_by_lesson_student_id(self, lesson_student_id: int) -> List[Homework]:
        """Получает список ДЗ по ID связи занятие-ученик"""
        stmt = select(Homework).where(Homework.lesson_student_id == lesson_student_id)
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

    async def delete_homework(self, homework_id: int) -> Homework | None:
        """Удаляет ДЗ по ее ID"""
        stmt = delete(Homework).where(Homework.id == homework_id).returning(Homework)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
