"""Explicit second disposable target, never a fallback for retained test55432.

F01.2 runner constructs this engine directly, without reading any env files.
The caller must also verify container labels before starting the test runner.
"""
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.engine import Connection, make_url

F012_URL = 'postgresql+asyncpg://lgg_f012_app:f012-synthetic-app@127.0.0.1:55433/lgg_f012'


def require_f012_url(url) -> None:
    parsed = make_url(url)
    if (parsed.drivername, parsed.host, parsed.port, parsed.database, parsed.username, bool(parsed.query)) != (
            'postgresql+asyncpg', '127.0.0.1', 55433, 'lgg_f012', 'lgg_f012_app', False):
        raise RuntimeError('Refusing operation outside dedicated F01.2 synthetic target')


def require_f012_connection(connection: Connection) -> None:
    require_f012_url(connection.engine.url)
    identity = connection.execute(text('SELECT current_database(), current_user, rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user')).one()
    if tuple(identity) != ('lgg_f012', 'lgg_f012_app', False, False, False):
        raise RuntimeError('Refusing unexpected actual F01.2 SQL identity/role')


async def require_f012_session(session, engine, media: Path, allocated: Path) -> None:
    require_f012_url(engine.url)
    if session.bind is not engine or media.is_symlink() or media.resolve() != allocated.resolve():
        raise RuntimeError('Refusing mismatched engine/session or nonallocated media')
    if not media.resolve().is_relative_to(Path('/tmp').resolve()):
        raise RuntimeError('F01.2 media must be a newly allocated temporary directory')
    await (await session.connection()).run_sync(require_f012_connection)
