"""Explicit disposable targets, never a fallback for retained test55432.

Synthetic runners construct their engines directly, without reading any env files.
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


F013_URL = 'postgresql+asyncpg://lgg_f013_app:f013-synthetic-app@127.0.0.1:55434/lgg_f013'


def require_f013_url(url) -> None:
    parsed = make_url(url)
    if (parsed.drivername, parsed.host, parsed.port, parsed.database, parsed.username, bool(parsed.query)) != (
            'postgresql+asyncpg', '127.0.0.1', 55434, 'lgg_f013', 'lgg_f013_app', False):
        raise RuntimeError('Refusing operation outside dedicated F01.3 synthetic target')


def require_f013_connection(connection: Connection) -> None:
    require_f013_url(connection.engine.url)
    identity = connection.execute(text('SELECT current_database(), current_user, rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user')).one()
    if tuple(identity) != ('lgg_f013', 'lgg_f013_app', False, False, False):
        raise RuntimeError('Refusing unexpected actual F01.3 SQL identity/role')


async def require_f013_session(session, engine, media: Path, allocated: Path) -> None:
    require_f013_url(engine.url)
    if session.bind is not engine or media.is_symlink() or media.resolve() != allocated.resolve():
        raise RuntimeError('Refusing mismatched engine/session or nonallocated media')
    if not media.resolve().is_relative_to(Path('/tmp').resolve()):
        raise RuntimeError('F01.3 media must be a newly allocated temporary directory')
    await (await session.connection()).run_sync(require_f013_connection)


F014_URL = 'postgresql+asyncpg://lgg_f014_app:f014-synthetic-app@127.0.0.1:55435/lgg_f014'


def require_f014_url(url) -> None:
    parsed = make_url(url)
    if (parsed.drivername, parsed.host, parsed.port, parsed.database, parsed.username, bool(parsed.query)) != (
            'postgresql+asyncpg', '127.0.0.1', 55435, 'lgg_f014', 'lgg_f014_app', False):
        raise RuntimeError('Refusing operation outside dedicated F01.4 synthetic target')


def require_f014_connection(connection: Connection) -> None:
    require_f014_url(connection.engine.url)
    identity = connection.execute(text('SELECT current_database(), current_user, rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user')).one()
    if tuple(identity) != ('lgg_f014', 'lgg_f014_app', False, False, False):
        raise RuntimeError('Refusing unexpected actual F01.4 SQL identity/role')


async def require_f014_session(session, engine, media: Path, allocated: Path) -> None:
    require_f014_url(engine.url)
    if session.bind is not engine or media.is_symlink() or media.resolve() != allocated.resolve():
        raise RuntimeError('Refusing mismatched engine/session or nonallocated media')
    if not media.resolve().is_relative_to(Path('/tmp').resolve()):
        raise RuntimeError('F01.4 media must be a newly allocated temporary directory')
    await (await session.connection()).run_sync(require_f014_connection)


F014_VERIFY_URL = 'postgresql+asyncpg://lgg_f014_verify_app:f014_verify-synthetic-app@127.0.0.1:55436/lgg_f014_verify'


def require_f014_verify_url(url) -> None:
    parsed = make_url(url)
    if (parsed.drivername, parsed.host, parsed.port, parsed.database, parsed.username, bool(parsed.query)) != (
            'postgresql+asyncpg', '127.0.0.1', 55436, 'lgg_f014_verify', 'lgg_f014_verify_app', False):
        raise RuntimeError('Refusing operation outside dedicated F01.4 verification synthetic target')


def require_f014_verify_connection(connection: Connection) -> None:
    require_f014_verify_url(connection.engine.url)
    identity = connection.execute(text('SELECT current_database(), current_user, rolsuper, rolcreatedb, rolcreaterole FROM pg_roles WHERE rolname=current_user')).one()
    if tuple(identity) != ('lgg_f014_verify', 'lgg_f014_verify_app', False, False, False):
        raise RuntimeError('Refusing unexpected actual F01.4 SQL identity/role')


async def require_f014_verify_session(session, engine, media: Path, allocated: Path) -> None:
    require_f014_verify_url(engine.url)
    if session.bind is not engine or media.is_symlink() or media.resolve() != allocated.resolve():
        raise RuntimeError('Refusing mismatched engine/session or nonallocated media')
    if not media.resolve().is_relative_to(Path('/tmp').resolve()):
        raise RuntimeError('F01.4 media must be a newly allocated temporary directory')
    await (await session.connection()).run_sync(require_f014_verify_connection)
