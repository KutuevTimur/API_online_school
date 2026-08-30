import os
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, AsyncEngine
from sqlalchemy.orm import sessionmaker

from src.core.config.base import init_env


class Config:
    def __init__(self):
        init_env()

        self.env = EnvConfig.build()
        self.db_connection = DbConnectionConfig.build(self.env)
        self.paths = PathsConfig.build()
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

    redis_host: str
    redis_port: int
    redis_url: str

    mode: str

    @classmethod
    def build(cls) -> "EnvConfig":
        redis_host = os.environ['REDIS_HOST']
        redis_port = int(os.environ['REDIS_PORT'])

        return cls(
            secret_key=os.environ['SECRET_KEY'],
            password_for_admin=os.environ['PASSWORD_FOR_ADMIN'],
            db_host=os.environ['DB_HOST'],
            db_port=os.environ['DB_PORT'],
            db_user=os.environ['DB_USER'],
            db_password=os.environ['DB_PASSWORD'],
            db_name=os.environ['DB_NAME'],

            redis_host=redis_host,
            redis_port=redis_port,
            redis_url=f"redis://{redis_host}:{redis_port}",

            mode=os.environ['MODE']
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
        sql_db_url = f'postgresql+asyncpg://{conf_env.db_user}:{conf_env.db_password}@{conf_env.db_host}:{conf_env.db_port}/{conf_env.db_name}'
        engine = create_async_engine(sql_db_url)

        return cls(
            postgres_server_url=f'postgresql+asyncpg://{conf_env.db_user}:{conf_env.db_password}@{conf_env.db_host}:{conf_env.db_port}/postgres',
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
    def build(cls, postscript: Optional[str] = '') -> "PathsConfig":
        base = Path(__file__).resolve().parents[3]

        media = base / Path(f"media{postscript}")
        avatars_users = media / Path(f"avatars_users{postscript}")
        avatars_courses = media / Path(f"avatars_courses{postscript}")
        lectures = media / Path(f"lectures{postscript}")
        homework = media / Path(f"homework{postscript}")
        homework_submissions = media / Path(f"homework_submissions{postscript}")
        temp = media / Path(f"temp{postscript}")

        media.mkdir(exist_ok=True)
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
    for_convert_image: List[str] = ["jpg", ".jpeg", "gif", ".png", "webp", "heic", "heif"]
    for_convert_pdf: List[str] = ["jpg", ".jpeg", "gif", ".png", "webp", "heic", "heif", "doc", "docx", "odt", "txt"]

    @classmethod
    def build(cls) -> "AllowedExtensions":
        return cls(
            for_convert_image=["jpg", ".jpeg", "gif", ".png", "webp", "heic", "heif"],
            for_convert_pdf=["jpg", ".jpeg", "gif", ".png", "webp", "heic", "heif", "doc", "docx", "odt", "txt"],
        )
