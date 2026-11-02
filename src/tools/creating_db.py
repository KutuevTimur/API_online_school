import asyncio
import tempfile
from pathlib import Path
from src.core.config import Config
from src.core.config.test_guard import require_test_config
from src.core.database.database import Base
import src.modules.db_models  # noqa: F401


async def create_database(conf: Config) -> None:
    """Legacy test schema setup; database/role are provisioned only by Compose."""
    require_test_config(conf)
    async with conf.db_connection.engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    with tempfile.TemporaryDirectory(prefix="lgg-test-tool-") as media:
        conf = Config(test=True, media_root=Path(media))
        try:
            await create_database(conf)
        finally:
            await conf.db_connection.engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
