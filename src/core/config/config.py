from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import URL
from src.core.config.test_guard import require_test_target

from src.core.config.base import init_env


class Config:
    def __init__(self, *, test: bool = False, media_root: Path | None = None):
        values = init_env(test=test)
        self.env = EnvConfig.build(values)
        if test and self.env.mode != "TEST":
            raise RuntimeError("Test config requires MODE=TEST")
        if self.env.mode == "TEST":
            require_test_target(self.env)
            if media_root is None:
                raise RuntimeError("Test config requires an explicit temporary media root")
        self.paths = PathsConfig.build(media_root=media_root or values.get("MEDIA_ROOT"))
        self.db_connection = DbConnectionConfig.build(self.env)
        self.tokens = TokensConfig.build()
        self.allowed_extensions = AllowedExtensions.build()


class EnvConfig(BaseModel):
    secret_key: str
    password_for_admin: str

    db_host: str
    db_port: str
    db_user: str
    db_password: str
    db_name: str

    redis_host: str | None = None
    redis_port: int | None = None
    redis_url: str | None = None
    mode: str
    allow_test_db_reset: str = "0"

    @classmethod
    def build(cls, values: dict[str, str]) -> "EnvConfig":
        return cls(
            secret_key=values['SECRET_KEY'],
            password_for_admin=values['PASSWORD_FOR_ADMIN'],
            db_host=values['DB_HOST'], db_port=values['DB_PORT'],
            db_user=values['DB_USER'], db_password=values['DB_PASSWORD'],
            db_name=values['DB_NAME'], mode=values['MODE'],
            allow_test_db_reset=values.get('ALLOW_TEST_DB_RESET', '0'),
        )



class DbConnectionConfig(BaseModel):
    postgres_server_url: str  # URL для подключения к серверу PostgresSQL без указания конкретной базы данных
    sql_db_url: str
    engine: AsyncEngine
    session_local: sessionmaker

    model_config = ConfigDict(
        arbitrary_types_allowed=True  # Разрешаем произвольные типы
    )

    @classmethod
    def build(cls, conf_env: EnvConfig) -> "DbConnectionConfig":
        url = URL.create("postgresql+asyncpg", username=conf_env.db_user,
                         password=conf_env.db_password, host=conf_env.db_host,
                         port=int(conf_env.db_port), database=conf_env.db_name)
        sql_db_url = url.render_as_string(hide_password=False)
        if conf_env.mode == "TEST":
            require_test_target(conf_env, sql_db_url)
        engine = create_async_engine(sql_db_url)

        return cls(
            postgres_server_url=url.set(database="postgres").render_as_string(hide_password=False),
            sql_db_url=sql_db_url,
            engine=engine,
            session_local=sessionmaker(
                engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False
            )
        )


class PathsConfig(BaseModel):
    base: Path
    media: Path
    avatars_users: Path
    avatars_courses: Path
    lectures: Path
    homework: Path
    homework_submissions: Path
    temp: Path

    @classmethod
    def build(cls, postscript: Optional[str] = '', media_root: Path | str | None = None) -> "PathsConfig":
        base = Path(__file__).resolve().parents[3]

        media = Path(media_root).resolve() if media_root else base / Path(f"media{postscript}")
        avatars_users = media / Path(f"avatars_users{postscript}")
        avatars_courses = media / Path(f"avatars_courses{postscript}")
        lectures = media / Path(f"lectures{postscript}")
        homework = media / Path(f"homework{postscript}")
        homework_submissions = media / Path(f"homework_submissions{postscript}")
        temp = media / Path(f"temp{postscript}")

        media.mkdir(parents=True, exist_ok=True)
        avatars_users.mkdir(exist_ok=True)
        avatars_courses.mkdir(exist_ok=True)
        lectures.mkdir(exist_ok=True)
        homework.mkdir(exist_ok=True)
        homework_submissions.mkdir(exist_ok=True)
        temp.mkdir(exist_ok=True)

        return cls(
            base=base,
            media=media,
            avatars_users=avatars_users,
            avatars_courses=avatars_courses,
            lectures=lectures,
            homework=homework,
            homework_submissions=homework_submissions,
            temp=temp,
        )


class TokensConfig(BaseModel):
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    algorithm: str

    @classmethod
    def build(cls) -> "TokensConfig":
        return cls(
            access_token_expire_minutes=30,
            refresh_token_expire_days=30,
            algorithm="HS256",
        )


class AllowedExtensions(BaseModel):
    for_convert_image: List[str] = ["webp", "jpg", ".jpeg", "gif", ".png", "heic", "heif"]
    for_convert_pdf: List[str] = ["jpg", ".jpeg", "gif", ".png", "webp", "heic", "heif", "doc", "docx", "odt", "txt"]

    @classmethod
    def build(cls) -> "AllowedExtensions":
        return cls(
            for_convert_image=["jpg", ".jpeg", "gif", ".png", "webp", "heic", "heif"],
            for_convert_pdf=["pdf", "jpg", ".jpeg", "gif", ".png", "webp", "heic", "heif", "doc", "docx", "odt", "txt"],
        )
