"""One local periodic worker; PostgreSQL SKIP LOCKED makes retries multi-worker safe."""
import asyncio
import logging

from src.core.config import Config
from src.modules.course_lifecycle.repository import LifecycleRepository
from src.modules.course_lifecycle.service import LifecycleService
from src.modules.files.maintenance import OrphanReconciliation, require_local_maintenance, queue_purged_backups

logger = logging.getLogger(__name__)


async def maintenance_once(config: Config) -> None:
    require_local_maintenance(config)
    async with config.db_connection.session_local() as session:
        # Reconciliation only queues stale owned UUIDs. Cleanup rechecks live refs.
        await queue_purged_backups(config,session)
        await OrphanReconciliation(session,config).run(apply=True)
        await LifecycleService(LifecycleRepository(session),config)._cleanup(100)


async def maintenance_worker(config: Config) -> None:
    while True:
        try:
            await maintenance_once(config)
        except asyncio.CancelledError:
            raise
        except Exception:
            # No paths, display names, SQL parameters or user contents in logs.
            logger.warning('Local file maintenance failed; will retry')
        await asyncio.sleep(60)
