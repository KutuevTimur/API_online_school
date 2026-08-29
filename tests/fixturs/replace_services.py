import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from helpers import test_crypto_context
from src.modules.handlers_files.compression_images import CompressionImages
from src.modules.handlers_files.converter_images import HandlerImages
from src.modules.path_builder import PathBuilder
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository
from src.modules.users.repository import UsersRepository
from src.modules.users.service import UsersService


@pytest_asyncio.fixture(scope="function")
async def user_service_fixture(session_db: AsyncSession, config_fix) -> UsersService:
    return UsersService(
        users_repo=UsersRepository(session=session_db),
        teacher_repo=TeacherRepository(session=session_db),
        student_repo=StudentRepository(session=session_db),
        cr_context=test_crypto_context,
        path_builder=PathBuilder(config=config_fix),
        handler_images=HandlerImages(config=config_fix),
        compression_images=CompressionImages(config=config_fix),
        session_db=session_db,
    )
