from typing import List, Tuple, Optional
from datetime import datetime
from sqlalchemy import select, delete, update, func
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

    async def get_all_by_lesson_student_id(
        self, 
        lesson_student_id: int,
        limit: int = 100,
        offset: int = 0,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sort_date: str = "desc"
    ) -> Tuple[List[Lecture], int]:
        """Получает список лекций по ID связи занятие-ученик с фильтрацией, пагинацией и сортировкой"""
        stmt = select(Lecture).where(Lecture.lesson_student_id == lesson_student_id)
        count_stmt = select(func.count()).select_from(Lecture).where(Lecture.lesson_student_id == lesson_student_id)

        if from_date:
            stmt = stmt.where(Lecture.created_at >= from_date)
            count_stmt = count_stmt.where(Lecture.created_at >= from_date)
            
        if to_date:
            stmt = stmt.where(Lecture.created_at <= to_date)
            count_stmt = count_stmt.where(Lecture.created_at <= to_date)
            
        if sort_date.lower() == "asc":
            stmt = stmt.order_by(Lecture.created_at.asc())
        else:
            stmt = stmt.order_by(Lecture.created_at.desc())
            
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        total_result = await self.session.execute(count_stmt)
        
        return list(result.scalars().all()), total_result.scalar() or 0

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
