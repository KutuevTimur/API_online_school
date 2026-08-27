import os
from pathlib import Path

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


class EnvConfig(BaseModel):
    secret_key: str

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

    @classmethod
    def build(cls) -> "PathsConfig":
        base = Path(__file__).resolve().parents[3]
        media = base / Path("media")

        media.mkdir(exist_ok=True)

        return cls(
            base=base,
            media=media,
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
