from typing import List, Tuple, Optional
from datetime import datetime

from sqlalchemy import select, update, delete, func, desc, asc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import BaseRepository
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

    async def get_by_submission_id(self, submission_id: int) -> HomeworkSubmission | None:
        stmt = (
            select(HomeworkSubmission)
            .where(HomeworkSubmission.id == submission_id)
            .options(selectinload(HomeworkSubmission.files))
        )
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
        sort_date: str = "desc"
    ) -> Tuple[List[HomeworkSubmission], int]:
        count_over = func.count().over().label('total_count')
        
        stmt = select(HomeworkSubmission, count_over).where(
            HomeworkSubmission.homework_id == homework_id
        )

        if sort_date.lower() == "asc":
            stmt = stmt.order_by(HomeworkSubmission.created_at.asc())
        else:
            stmt = stmt.order_by(HomeworkSubmission.created_at.desc())
            
        stmt = stmt.limit(limit).offset(offset)
        stmt = stmt.options(selectinload(HomeworkSubmission.files))

        result = await self.session.execute(stmt)
        rows = result.all()

        if not rows:
            return [], 0
            
        total = rows[0][1]
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
