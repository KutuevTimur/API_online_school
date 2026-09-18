import pytest_asyncio

from fixturs import *
from src.modules.db_models import *
from src.tools.creating_db import create_database

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete


@pytest_asyncio.fixture(scope='session', autouse=True)
async def start_test(config_fix, app_fastapi):
    if config_fix.env.mode != "TEST":
        raise RuntimeError("Пожалуйста используйте .env файл для тестов!")

    await create_database()


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clearing_db(session_db: AsyncSession):
    """Очиста бд перед тестами"""
    # Удаляем зависимости в нужном порядке
    await session_db.execute(delete(HomeworkSubmission))
    await session_db.execute(delete(Homework))
    await session_db.execute(delete(Lecture))
    await session_db.execute(delete(LessonStudent))
    await session_db.execute(delete(Lesson))
    await session_db.execute(delete(StudentCourse))
    await session_db.execute(delete(Course))
    await session_db.execute(delete(RefreshToken))
    await session_db.execute(delete(Teacher))
    await session_db.execute(delete(Student))
    await session_db.execute(delete(User))
    await session_db.commit()
