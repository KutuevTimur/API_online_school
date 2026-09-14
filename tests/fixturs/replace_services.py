import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from helpers import test_crypto_context
from src.modules.courses.repository import CourseRepository
from src.modules.courses.service import CoursesService
from src.modules.handlers_files.compression_images import CompressionImages
from src.modules.handlers_files.converter_images import HandlerImages
from src.modules.handlers_files.handler_documents import HandlerDocuments
from src.modules.path_builder import PathBuilder
from src.modules.student_courses.repository import StudentCoursesRepository
from src.modules.students.repository import StudentRepository
from src.modules.students.service import StudentService
from src.modules.teachers.repository import TeacherRepository
from src.modules.teachers.service import TeacherService
from src.modules.users.repository import UsersRepository
from src.modules.users.service import UsersService


@pytest_asyncio.fixture(scope="function")
async def user_service_fixture(session_db: AsyncSession, config_fix) -> UsersService:
    teacher_repo = TeacherRepository(session=session_db)
    student_repo = StudentRepository(session=session_db)
    return UsersService(
        users_repo=UsersRepository(session=session_db),
        teacher_repo=teacher_repo,
        teacher_service=TeacherService(teacher_repo=teacher_repo, session_db=session_db),
        student_repo=student_repo,
        student_service=StudentService(student_repo=student_repo, session_db=session_db),
        cr_context=test_crypto_context,
        path_builder=PathBuilder(config=config_fix),
        handler_images=HandlerImages(config=config_fix),
        compression_images=CompressionImages(config=config_fix),
        session_db=session_db,
    )


@pytest_asyncio.fixture(scope="function")
async def courses_service_fixture(session_db: AsyncSession, config_fix) -> CoursesService:
    teacher_repo = TeacherRepository(session=session_db)
    student_repo = StudentRepository(session=session_db)
    return CoursesService(
        course_repo=CourseRepository(session=session_db),
        teacher_repo=teacher_repo,
        teacher_service=TeacherService(teacher_repo=teacher_repo, session_db=session_db),
        student_repo=student_repo,
        student_service=StudentService(student_repo=student_repo, session_db=session_db),
        path_builder=PathBuilder(config=config_fix),
        handler_images=HandlerImages(config=config_fix),
        compression_images=CompressionImages(config=config_fix),
        session_db=session_db,
        student_courses_repo=StudentCoursesRepository(session=session_db),
    )


@pytest_asyncio.fixture(scope="function")
async def compression_images_fixture(config_fix) -> CompressionImages:
    return CompressionImages(config=config_fix)


@pytest_asyncio.fixture(scope="function")
async def handler_images_fixture(config_fix) -> HandlerImages:
    return HandlerImages(config=config_fix)


@pytest_asyncio.fixture(scope="function")
async def handler_documents_fixture(config_fix) -> HandlerDocuments:
    return HandlerDocuments(config=config_fix)
