from src.modules.check_permission.repository import submission_scope
from sqlalchemy.orm import with_loader_criteria
from typing import List, Tuple, Optional
from datetime import datetime

from sqlalchemy import select, update, delete, func, desc, asc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.homework_submissions.models import HomeworkSubmission, HomeworkSubmissionFile
from src.modules.homework_submissions.models_dto import HomeworkSubmissionRequestDTO, HomeworkSubmissionFileRequestDTO


class HomeworkSubmissionsRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=HomeworkSubmission,
        )

    async def add_submission(self, data: HomeworkSubmissionRequestDTO) -> HomeworkSubmission:
        return self.add(data)

    async def add_submission_files(self, files_data: List[HomeworkSubmissionFileRequestDTO]) -> None:
        if not files_data:
            return
        files = [HomeworkSubmissionFile(**file.model_dump()) for file in files_data]
        self.session.add_all(files)

    async def get_by_submission_id(self, submission_id: int, actor=None, lock: bool = False) -> HomeworkSubmission | None:
        stmt = (
            select(HomeworkSubmission)
            .where(HomeworkSubmission.id == submission_id)
            .options(selectinload(HomeworkSubmission.files))
        )
        if lock:
            stmt = stmt.with_for_update().execution_options(populate_existing=True)
        if actor is not None:
            file_predicate = submission_scope(HomeworkSubmissionFile, actor.id, actor.role)
            stmt = stmt.where(submission_scope(HomeworkSubmission, actor.id, actor.role)).options(
                with_loader_criteria(HomeworkSubmissionFile, file_predicate)).execution_options(populate_existing=True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_homework_and_attempt(self, homework_id: int, attempt_number: int) -> HomeworkSubmission | None:
        stmt = (
            select(HomeworkSubmission)
            .where(HomeworkSubmission.homework_id == homework_id)
            .where(HomeworkSubmission.attempt_number == attempt_number)
            .options(selectinload(HomeworkSubmission.files))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_max_attempt_number(self, homework_id: int) -> int:
        stmt = select(func.max(HomeworkSubmission.attempt_number)).where(HomeworkSubmission.homework_id == homework_id)
        result = await self.session.scalar(stmt)
        return result or 0

    async def get_submissions_by_homework_id(
        self,
        homework_id: int,
        limit: int = 100,
        offset: int = 0,
        sort_date: str = "desc",
        actor=None,
    ) -> Tuple[List[HomeworkSubmission], int]:
        scope = submission_scope(HomeworkSubmission, actor.id, actor.role) if actor else True
        total = await self.session.scalar(select(func.count()).select_from(HomeworkSubmission).where(
            HomeworkSubmission.homework_id == homework_id, scope)) or 0
        count_over = func.count().over().label('total_count')
        
        stmt = select(HomeworkSubmission, count_over).where(
            HomeworkSubmission.homework_id == homework_id, scope
        )

        if sort_date.lower() == "asc":
            stmt = stmt.order_by(HomeworkSubmission.created_at.asc())
        else:
            stmt = stmt.order_by(HomeworkSubmission.created_at.desc())
            
        stmt = stmt.limit(limit).offset(offset)
        stmt = stmt.options(selectinload(HomeworkSubmission.files))

        if actor is not None:
            file_predicate = submission_scope(HomeworkSubmissionFile, actor.id, actor.role)
            stmt = stmt.where(submission_scope(HomeworkSubmission, actor.id, actor.role)).options(
                with_loader_criteria(HomeworkSubmissionFile, file_predicate)).execution_options(populate_existing=True)
        result = await self.session.execute(stmt)
        rows = result.all()

        if not rows:
            return [], total
            
        submissions = [row[0] for row in rows]
        
        return submissions, total

    async def update_submission(self, submission_id: int, values: dict) -> HomeworkSubmission:
        stmt = (
            update(HomeworkSubmission)
            .where(HomeworkSubmission.id == submission_id)
            .values(**values)
            .returning(HomeworkSubmission)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete_submission(self, submission_id: int) -> HomeworkSubmission | None:
        stmt = (
            delete(HomeworkSubmission)
            .where(HomeworkSubmission.id == submission_id)
            .returning(HomeworkSubmission)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_submission_files(self, submission_id: int) -> List[HomeworkSubmissionFile]:
        stmt = (
            delete(HomeworkSubmissionFile)
            .where(HomeworkSubmissionFile.submission_id == submission_id)
            .returning(HomeworkSubmissionFile)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_submission_file_by_id(self, file_id: int) -> HomeworkSubmissionFile | None:
        stmt = (
            select(HomeworkSubmissionFile)
            .where(HomeworkSubmissionFile.id == file_id)
            .options(
                selectinload(HomeworkSubmissionFile.submission)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def lock_homework(self, homework_id: int) -> None:
        from src.modules.homeworks.models import Homework
        await self.session.scalar(select(Homework).where(Homework.id == homework_id).with_for_update())

    async def working_submission(self, homework_id: int) -> HomeworkSubmission | None:
        return await self.session.scalar(select(HomeworkSubmission).where(
            HomeworkSubmission.homework_id == homework_id, HomeworkSubmission.is_working.is_(True)))

    async def remove_file(self, file: HomeworkSubmissionFile) -> None:
        from src.modules.course_lifecycle.models import FileDeletion
        paths = {file.original_file_path, file.pdf_file_path} - {None}
        self.session.add_all([FileDeletion(path=p) for p in sorted(paths)])
        await self.session.delete(file)

    async def file_count(self, submission_id: int) -> int:
        return await self.session.scalar(select(func.count()).select_from(HomeworkSubmissionFile).where(
            HomeworkSubmissionFile.submission_id == submission_id)) or 0
