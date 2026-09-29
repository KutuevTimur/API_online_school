import asyncio
import asyncpg
from src.core.config import Config

async def drop_schema():
    conf = Config()
    url = conf.db_connection.sql_db_url.replace("postgresql+asyncpg", "postgresql")
    conn = await asyncpg.connect(url)
    await conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    await conn.close()
    print("Schema dropped")

if __name__ == "__main__":
    asyncio.run(drop_schema())