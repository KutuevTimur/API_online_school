"""Read-only verification of actual disposable database/session/media target."""
import asyncio
import tempfile
from pathlib import Path
from sqlalchemy import text
from src.core.config import create_config
from src.core.config.test_guard import require_test_config

async def main() -> None:
    with tempfile.TemporaryDirectory(prefix='lgg-test-media-preflight-') as root:
        c = create_config(test=True, media_root=Path(root))
        require_test_config(c)
        async with c.db_connection.session_local() as s:
            assert s.bind is c.db_connection.engine
            row = (await s.execute(text('SELECT current_database(), current_user, rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user'))).one()
            assert tuple(row) == ('lgg_test', 'lgg_test_app', False, False, False)
            assert c.paths.media == Path(root).resolve()
            print('PASS actual engine/session guard; SQL lgg_test/lgg_test_app restricted; temporary media')
        await c.db_connection.engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())
