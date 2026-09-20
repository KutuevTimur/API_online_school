from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.modules.homework_submissions.models import HomeworkSubmission
from src.modules.homework_submissions.models_dto import HomeworkSubmissionResponseDTO
from tests.modules.homework_submissions.fixtures.models_dto import CreateHomeworkSubmissionFixtureDTO

from tests.modules.homeworks.fixtures.factory import create_homework_factory
from tests.modules.homeworks.fixtures.models_dto import CreateHomeworkFixtureDTO


async def create_homework_submission_factory(
    session_db: AsyncSession,
    crypto_context: CryptContext,
    new_submission: CreateHomeworkSubmissionFixtureDTO,
) -> HomeworkSubmissionResponseDTO:

    if new_submission.homework_id is None:
        homework = await create_homework_factory(
            session_db, crypto_context, CreateHomeworkFixtureDTO()
        )
        new_submission.homework_id = homework.id

    submission_db = HomeworkSubmission(**new_submission.model_dump())
    session_db.add(submission_db)
    await session_db.commit()
    
    stmt = select(HomeworkSubmission).options(selectinload(HomeworkSubmission.files)).where(HomeworkSubmission.id == submission_db.id)
    res = await session_db.execute(stmt)
    submission_db = res.scalar_one()

    return HomeworkSubmissionResponseDTO.model_validate(submission_db)
