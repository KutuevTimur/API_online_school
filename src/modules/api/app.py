from contextlib import asynccontextmanager
import asyncio
from contextlib import suppress

from fastapi import FastAPI
from passlib.context import CryptContext

from src.core.config import create_config, Config
from src.modules.api.exception_handler import register_exception_handlers
from src.modules.auth.views import router as auth_router
from src.modules.courses.views import router as courses_router
from src.modules.student_courses.views import router as student_courses_router
from src.modules.users.views import router as user_router
from src.modules.lessons.views import router as lessons_router
from src.modules.lesson_students.views import router as lesson_students_router
from src.modules.lectures.views import router as lectures_router
from src.modules.homeworks.views import router as homeworks_router
from src.modules.homework_submissions.views import router as homework_submissions_router


from src.modules.teacher_students.views import router as teacher_students_router


from src.modules.account_invitations.views import router as invitations_router

from src.modules.course_lifecycle.views import router as lifecycle_router

from src.modules.homework_placements.views import router as homework_placements_router


def _include_routers(app: FastAPI) -> FastAPI:
    from src.modules.files.views import router as files_router
    app.include_router(files_router)
    app.include_router(lifecycle_router)
    app.include_router(invitations_router)
    app.include_router(teacher_students_router)
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(courses_router)
    app.include_router(student_courses_router)
    app.include_router(lessons_router)
    app.include_router(lesson_students_router)
    app.include_router(lectures_router)
    app.include_router(homeworks_router)
    app.include_router(homework_placements_router)
    app.include_router(homework_submissions_router)
    return app


def init_fastapi_app(config: Config | None = None) -> FastAPI:
    app = FastAPI(
        title="Auth Service",
        lifespan=lifespan
    )

    from src.modules.storage.middleware import MultipartBodyLimitMiddleware
    app.add_middleware(MultipartBodyLimitMiddleware)
    app.state.config = config if config is not None else create_config()
    register_exception_handlers(app)

    _include_routers(app)

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = app.state.config
    app.state.cr_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto"
    )

    worker = None
    if config.file_maintenance_enabled:
        from src.modules.files.worker import maintenance_worker
        worker = asyncio.create_task(maintenance_worker(config))

    try:
        yield
    finally:
        if worker is not None:
            worker.cancel()
            with suppress(asyncio.CancelledError):
                await worker
        await config.db_connection.engine.dispose()
