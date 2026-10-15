from src.modules.check_permission.repository import material_scope
from src.modules.users.models import UserRole
from typing import List
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.homeworks.models import Homework
from src.modules.lesson_students.models import LessonStudent
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
        return self.add(data)

    async def get_by_id(self, homework_id: int) -> Homework | None:
        return await super().get_by_id(Homework, homework_id)

    async def get_all_by_lesson_student_id(self, lesson_student_id: int, actor=None) -> List[Homework]:
        stmt = select(Homework).where(Homework.lesson_student_id == lesson_student_id)
        if actor is not None:
            stmt = stmt.where(material_scope(Homework, actor.id, actor.role))
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
        
    async def get_all_by_student_id(self, student_id: int, actor=None) -> List[Homework]:
        """Получить все домашние задания студента по всем урокам / курсам (JOIN к lesson_students)"""
        stmt = select(Homework).join(
            LessonStudent, Homework.lesson_student_id == LessonStudent.id
        ).where(LessonStudent.student_id == student_id)
        if actor is not None:
            stmt = stmt.where(material_scope(Homework, actor.id, actor.role))
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

    async def has_submissions(self, homework_id: int) -> bool:
        from sqlalchemy import exists
        from src.modules.homework_submissions.models import HomeworkSubmission
        return bool(await self.session.scalar(select(exists().where(
            HomeworkSubmission.homework_id == homework_id))))

    async def delete_homework(self, homework_id: int) -> Homework | None:
        stmt = delete(Homework).where(Homework.id == homework_id).returning(Homework)
        result = await self.session.execute(stmt)
        deleted = result.scalar_one_or_none()
        if deleted:
            from src.modules.files.repository import FileAssetsRepository
            await FileAssetsRepository(self.session).prune(
                {deleted.original_asset_id, deleted.download_asset_id} - {None})
        return deleted
