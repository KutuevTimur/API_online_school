import pytest_asyncio

from src.modules.homework_submissions.models_dto import HomeworkSubmissionResponseDTO
from tests.helpers import test_crypto_context
from tests.modules.homework_submissions.fixtures.factory import create_homework_submission_factory
from tests.modules.homework_submissions.fixtures.models_dto import CreateHomeworkSubmissionFixtureDTO


@pytest_asyncio.fixture(scope="function")
async def create_homework_submission_fixture(not_open_session_db):
    async def _factory(
        new_submission: CreateHomeworkSubmissionFixtureDTO = CreateHomeworkSubmissionFixtureDTO(),
    ) -> HomeworkSubmissionResponseDTO:
        async with not_open_session_db() as session:
            submission = await create_homework_submission_factory(
                session_db=session,
                crypto_context=test_crypto_context,
                new_submission=new_submission,
            )
            return submission

    return _factory
