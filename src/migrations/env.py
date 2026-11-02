import asyncio
from logging.config import fileConfig

from sqlalchemy import pool, text
from tempfile import TemporaryDirectory
from pathlib import Path
from src.core.config.test_guard import require_test_config
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

from src.core.config import create_config
from src.core.database.database import Base

# ОСТАВИТЬ. НЕОБХОДИМО ДЛЯ ПОДГРУЗКИ МОДЕЛЕЙ
from src.modules.db_models import *

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.

config = context.config
# TEST uses the explicit guarded .env.test target. Media is unused by Alembic.
_external = config.attributes.get("connection")
if _external is None:
    _media = TemporaryDirectory(prefix="lgg-alembic-")
    app_config = create_config(media_root=Path(_media.name))
    if app_config.env.mode == "TEST":
        require_test_config(app_config)
    config.set_main_option("sqlalchemy.url",
                           app_config.db_connection.sql_db_url.replace("%", "%%"))
else:
    # Programmatic synthetic runner supplies a connection and its strict preflight.
    # No .env/.env.test or retained preview engine is constructed on this path.
    from src.core.config.synthetic_guard import require_f012_connection, require_f013_connection, require_f014_connection, require_f014_verify_connection
    if _external.engine.url.port == 55436:
        require_f014_verify_connection(_external)
    elif _external.engine.url.port == 55435:
        require_f014_connection(_external)
    elif _external.engine.url.port == 55434:
        require_f013_connection(_external)
    else:
        require_f012_connection(_external)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = Base.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    if connection.dialect.has_table(connection, "alembic_version"):
        revisions = set(connection.execute(text("SELECT version_num FROM alembic_version")).scalars())
        if "1c3d40e331ff" in revisions:
            raise RuntimeError(
                "Unsupported main baseline 1c3d40e331ff: stop; inventory and backup "
                "plus a separate migration plan required. Do not stamp or drop."
            )
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
            await connection.commit()
    finally:
        await connectable.dispose()
        await app_config.db_connection.engine.dispose()
        _media.cleanup()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    if _external is not None:
        do_run_migrations(_external)
    else:
        asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
