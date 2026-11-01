"""Standalone synthetic DB helper; never imports dangerous tests/conftest.py."""
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.core.config.synthetic_guard import F012_URL, require_f012_url, require_f012_connection


def engine():
    require_f012_url(F012_URL)
    return create_async_engine(F012_URL)


def migrate(connection, revision='head'):
    require_f012_connection(connection)
    config = Config('alembic.ini')
    config.attributes['connection'] = connection
    command.upgrade(config, revision)


def downgrade(connection, revision):
    require_f012_connection(connection)
    config = Config('alembic.ini')
    config.attributes['connection'] = connection
    command.downgrade(config, revision)
