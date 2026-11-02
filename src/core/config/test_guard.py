from pathlib import Path
from typing import Any, Callable
from sqlalchemy.engine import make_url


def require_test_target(env: Any, url: str | None = None) -> None:
    expected = ("TEST", "lgg_test", "lgg_test_app", "127.0.0.1", "55432", "1")
    actual = (env.mode, env.db_name, env.db_user, env.db_host, str(env.db_port),
              env.allow_test_db_reset)
    if actual != expected:
        raise RuntimeError("Refusing operation: not the explicit disposable test target")
    if url is not None:
        parsed = make_url(url)
        if (parsed.drivername, parsed.database, parsed.username, parsed.host,
                parsed.port, bool(parsed.query)) != (
                "postgresql+asyncpg", "lgg_test", "lgg_test_app", "127.0.0.1", 55432, False):
            raise RuntimeError("Refusing operation: actual URL differs from test target")


def guarded_operation(env: Any, url: str, factory: Callable[[], Any]) -> Any:
    require_test_target(env, url)
    return factory()


def remove_test_media(env: Any, url: str, media: Path, allocated: Path,
                      remover: Callable[[Path], Any]) -> None:
    require_test_target(env, url)
    if media.is_symlink() or media.resolve() != allocated.resolve():
        raise RuntimeError("Refusing removal outside allocated pytest media")
    remover(media)


def require_test_config(conf: Any) -> None:
    require_test_target(conf.env, conf.db_connection.sql_db_url)
    require_test_target(conf.env, str(conf.db_connection.engine.url))
    bind = conf.db_connection.session_local.kw.get("bind")
    if bind is not conf.db_connection.engine:
        raise RuntimeError("Refusing operation: session factory uses another engine")
