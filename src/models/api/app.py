from contextlib import asynccontextmanager

from fastapi import FastAPI
from passlib.context import CryptContext

from src.core.config import create_config
from src.models.api.exception_handler import register_exception_handlers
from src.models.auth.views import router as auth_router
from src.models.users.views import router as user_router


def _include_routers(app: FastAPI) -> FastAPI:
    app.include_router(auth_router)
    app.include_router(user_router)
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