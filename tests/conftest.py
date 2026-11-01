import pytest_asyncio

from fixturs import *
from src.modules.db_models import *
from src.tools.creating_db import create_database
from src.core.config.test_guard import require_test_config

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete


@pytest_asyncio.fixture(scope='session', autouse=True)
async def start_test(config_fix, app_fastapi):
    require_test_config(config_fix)
    await create_database(config_fix)


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clearing_db(session_db: AsyncSession, config_fix):
    """Очиста бд перед тестами"""
    require_test_config(config_fix)
    await session_db.execute(delete(Notification))
    await session_db.execute(delete(AuditEvent))
    await session_db.execute(delete(FileDeletion))
    await session_db.execute(delete(LifecycleAudit))
    await session_db.execute(delete(EnrollmentGap))
    await session_db.execute(delete(AccountInvitation))
    await session_db.execute(delete(AccountAudit))
    await session_db.execute(delete(AuthRateLimit))
    # Удаляем зависимости в нужном порядке
    await session_db.execute(delete(HomeworkSubmissionFile))
    await session_db.execute(delete(HomeworkSubmission))
    await session_db.execute(delete(HomeworkDeadlineEvent))
    await session_db.execute(delete(HomeworkPlacement))
    await session_db.execute(delete(Homework))
    await session_db.execute(delete(Lecture))
    await session_db.execute(delete(LessonStudent))
    await session_db.execute(delete(Lesson))
    await session_db.execute(delete(RegularLessonOperation))
    await session_db.execute(delete(RegularLessonSeries))
    await session_db.execute(delete(StudentCourse))
    await session_db.execute(delete(Course))
    await session_db.execute(delete(RefreshToken))
    await session_db.execute(delete(WeeklyLessonNorm))
    await session_db.execute(delete(TeacherStudent))
    await session_db.execute(delete(Teacher))
    await session_db.execute(delete(Student))
    await session_db.execute(delete(FileAsset))
    await session_db.execute(delete(User))
    await session_db.commit()
