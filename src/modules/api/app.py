from contextlib import asynccontextmanager

from fastapi import FastAPI
from passlib.context import CryptContext

from src.core.config import create_config
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


def _include_routers(app: FastAPI) -> FastAPI:
    app.include_router(auth_router)
    app.include_router(user_router)
    app.include_router(courses_router)
    app.include_router(student_courses_router)
    app.include_router(lessons_router)
    app.include_router(lesson_students_router)
    app.include_router(lectures_router)
    app.include_router(homeworks_router)
    app.include_router(homework_submissions_router)
    return app


def init_fastapi_app() -> FastAPI:
    app = FastAPI(
        title="Auth Service",
        lifespan=lifespan
    )

    app.state.config = create_config()
    register_exception_handlers(app)

    _include_routers(app)

    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = create_config()
    app.state.config = config
    app.state.cr_context = CryptContext(
        schemes=["bcrypt"],
        deprecated="auto"
    )

    try:
        yield
    finally:
        pass
