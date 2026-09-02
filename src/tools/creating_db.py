import asyncio
import logging

from sqlalchemy import text, Enum
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import Config

# Не удалять. Используется для подгрузки всех моделей БД
from src.core.database.database import Base
import src.modules.db_models  # noqa: F401

async def create_database():
    """Создает базу данных и все таблицы в ней (если существует, то ничего не произойдёт) """
    # Сначала подключаемся к серверу PostgreSQL без указания конкретной базы
    conf = Config()

    engine = create_async_engine(conf.db_connection.postgres_server_url, isolation_level="AUTOCOMMIT")

    try:
        # Проверяем существование базы данных и создаем если ее нет
        async with engine.connect() as conn:
            result = await conn.execute(
                text(f"SELECT 1 FROM pg_database WHERE datname = '{conf.env.db_name}'")
            )
            database_exists = result.scalar() == 1

            if not database_exists: # если БД нет
                logging.info(f"Creating database {conf.env.db_name}...")
                await conn.execute(text(f"CREATE DATABASE {conf.env.db_name}"))
                logging.info(f"Database {conf.env.db_name} created successfully")
            else:
                logging.info(f"Database {conf.env.db_name} already exists")
    except Exception as e:
        logging.error(f"Error checking/creating database: {e}")
        raise
    finally:
        await engine.dispose()

    # создаем таблицы в целевой базе данных
    engine = create_async_engine(conf.db_connection.sql_db_url)
    try:
        async with engine.begin() as conn:
            logging.info("Creating database tables...")
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
        logging.error(f"Error creating tables: {e}")
        raise
    finally:
        await engine.dispose()



if __name__ == "__main__":
    asyncio.run(create_database())
