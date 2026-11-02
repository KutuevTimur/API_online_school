import asyncio
import tempfile
from pathlib import Path
from src.core.config import Config
from src.core.config.test_guard import require_test_config
from src.core.database.database import Base
import src.modules.db_models  # noqa: F401


async def recreate() -> None:
    with tempfile.TemporaryDirectory(prefix="lgg-test-tool-") as media:
        conf = Config(test=True, media_root=Path(media))
        try:
            require_test_config(conf)
            async with conf.db_connection.engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
        finally:
            await conf.db_connection.engine.dispose()


if __name__ == "__main__":
    asyncio.run(recreate())
