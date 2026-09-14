from typing import List
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import BaseRepository
from src.modules.lectures.models import Lecture
from src.modules.lectures.models_dto import CreateLectureRequestDTO


class LecturesRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=Lecture,
        )

    async def add_lecture(
        self,
        data: CreateLectureRequestDTO,
    ) -> Lecture:
        """Добавляет запись лекции"""
        return self.add(data)

    async def get_by_id(self, lecture_id: int) -> Lecture | None:
        """Получает лекцию по ее ID"""
        return await super().get_by_id(Lecture, lecture_id)

    async def get_all_by_lesson_student_id(self, lesson_student_id: int) -> List[Lecture]:
        """Получает список лекций по ID связи занятие-ученик"""
        stmt = select(Lecture).where(Lecture.lesson_student_id == lesson_student_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

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
                pdf_file_path=pdf_file_path
            )
            .returning(Lecture)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_lecture(self, lecture_id: int) -> Lecture | None:
        """Удаляет лекцию по ее ID"""
        stmt = delete(Lecture).where(Lecture.id == lecture_id).returning(Lecture)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
