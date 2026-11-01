"""Standalone synthetic DB helper; never imports dangerous tests/conftest.py."""
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.core.config.synthetic_guard import F013_URL, require_f013_url, require_f013_connection


def engine():
    require_f013_url(F013_URL)
    return create_async_engine(F013_URL)


def migrate(connection, revision='head'):
    require_f013_connection(connection)
    config = Config('alembic.ini')
    config.attributes['connection'] = connection
    command.upgrade(config, revision)


def downgrade(connection, revision):
    require_f013_connection(connection)
    config = Config('alembic.ini')
    config.attributes['connection'] = connection
    command.downgrade(config, revision)
