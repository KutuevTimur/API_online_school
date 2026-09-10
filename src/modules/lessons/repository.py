from sqlalchemy import update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import BaseRepository
from src.modules.lessons.models import Lesson
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
        """Добавление новой записи занятия в сессию"""
        return self.add(data)

    async def get_lesson_by_id(self, lesson_id: int) -> Lesson | None:
        """Получение занятия по ID"""
        return await self.get_by_id(Lesson, lesson_id)

    async def update_student(
        self,
        lesson_id: int,
        values: dict,
    ) -> Lesson | None:
        """Обновление данных занятия по ID"""
        result_db = await self.session.execute(
            update(Lesson)
            .where(Lesson.id == lesson_id)
            .values(**values)
            .returning(Lesson)
        )
        return result_db.scalar_one_or_none()

    async def delete_student(self, lesson_id: int) -> Lesson | None:
        """Удаление студента по ID"""
        result_db = await self.session.execute(
            delete(Lesson)
            .where(Lesson.id == lesson_id)
            .returning(Lesson)
        )
        return result_db.scalar_one_or_none()