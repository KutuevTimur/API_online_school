import asyncio
from dotenv import load_dotenv

load_dotenv("../../.test.env", override=True)

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from src.core.config import Config
from src.core.database.database import Base

async def recreate():
    conf = Config()
    url = conf.db_connection.sql_db_url
    print("Recreating tables for DB:", url)
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS teacher_courses CASCADE;"))
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(recreate())