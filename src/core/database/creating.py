import logging
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text, Enum

from src.core.config import Config
from src.core.config.test_guard import require_test_config
from src.core.database.database import Base
import src.modules.db_models  # noqa: F401


async def create_database(conf: Config):
    """Создает базу данных и все таблицы в ней (если существует, то ничего не произойдёт) """
    if conf.env.mode == "TEST":
        require_test_config(conf)
        from src.tools.creating_db import create_database as create_test_schema
        return await create_test_schema(conf)
    # Сначала подключаемся к серверу PostgreSQL без указания конкретной базы
    engine = create_async_engine(conf.db_connection.postgres_server_url, isolation_level="AUTOCOMMIT")

    try:
        # Проверяем существование базы данных и создаем если ее нет
        async with engine.connect() as conn:
            result = await conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{conf.env.db_name}'")
            )
            database_exists = result.scalar() == 1

            if not database_exists: # если БД нет
                logging.info(f"Creating _database {conf.env.db_name}...")
                await conn.execute(text(f"CREATE DATABASE {conf.env.db_name}"))
                logging.info(f"Database {conf.env.db_name} created successfully")
            else:
                logging.info(f"Database {conf.env.db_name} already exists")
    except Exception as e:
        logging.exception(f"Error checking/creating _database: {e}")
        raise e
    finally:
        await engine.dispose()

    # создаем таблицы в целевой базе данных
    if conf.env.mode == "TEST":
        require_test_config(conf)
    engine = create_async_engine(conf.db_connection.sql_db_url, connect_args={"statement_cache_size": 0})
    try:
        async with engine.begin() as conn:
            logging.info("Creating _database tables...")
            await conn.run_sync(Base.metadata.create_all)
            for table in Base.metadata.tables.values():
                for column in table.columns:
                    if isinstance(column.type, Enum) and column.type.name:
                        for val in column.type.enums:
                            await conn.execute(
                                text(f"ALTER TYPE {column.type.name} ADD VALUE IF NOT EXISTS '{val}'")
                            )
            logging.info("Database tables created successfully")
    except Exception as e:
        logging.exception(f"Error creating tables: {e}")
        raise e
    finally:
        await engine.dispose()


async def create_table(conf: Config):
    """создает таблицы в целевой базе данных"""
    if conf.env.mode == "TEST":
        require_test_config(conf)
    engine = create_async_engine(conf.db_connection.sql_db_url, connect_args={"statement_cache_size": 0})
    try:
        async with engine.begin() as conn:
            logging.info("Creating core tables...")
            await conn.run_sync(Base.metadata.create_all)
            for table in Base.metadata.tables.values():
                for column in table.columns:
                    if isinstance(column.type, Enum) and column.type.name:
                        for val in column.type.enums:
                            await conn.execute(
                                text(f"ALTER TYPE {column.type.name} ADD VALUE IF NOT EXISTS '{val}'")
                            )
            logging.info("Database tables created successfully")
    except Exception as e:
        logging.exception(f"Error creating tables: {e}")
        raise e
    finally:
        await engine.dispose()
