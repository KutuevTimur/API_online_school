import asyncio
import tempfile
from pathlib import Path
from sqlalchemy import text
from src.core.config import Config
from src.core.config.test_guard import require_test_config
import src.modules.db_models  # noqa: F401


async def drop_schema() -> None:
    with tempfile.TemporaryDirectory(prefix="lgg-test-tool-") as media:
        conf = Config(test=True, media_root=Path(media))
        try:
            require_test_config(conf)
            async with conf.db_connection.engine.begin() as conn:
                await conn.execute(text("DROP SCHEMA public CASCADE"))
                await conn.execute(text("CREATE SCHEMA public AUTHORIZATION lgg_test_app"))
        finally:
            await conf.db_connection.engine.dispose()


if __name__ == "__main__":
    asyncio.run(drop_schema())
