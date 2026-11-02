"""Standalone synthetic DB helper; never imports dangerous tests/conftest.py."""
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
import os
from src.core.config import synthetic_guard as guards
TARGET = os.environ.get('LGG_SYNTHETIC_TASK', 'F013')
if TARGET not in {'F013', 'F014', 'F014_VERIFY', 'F014_UI_API'}:
    raise RuntimeError('Unknown synthetic task')
URL = getattr(guards, TARGET + '_URL')
require_url = getattr(guards, 'require_' + TARGET.lower() + '_url')
require_connection = getattr(guards, 'require_' + TARGET.lower() + '_connection')
require_session = getattr(guards, 'require_' + TARGET.lower() + '_session')
PORT = {'F013': 55434, 'F014': 55435, 'F014_VERIFY': 55436, 'F014_UI_API': 55437}[TARGET]


def engine():
    require_url(URL)
    return create_async_engine(URL)


def migrate(connection, revision='head'):
    require_connection(connection)
    config = Config('alembic.ini')
    config.attributes['connection'] = connection
    command.upgrade(config, revision)


def downgrade(connection, revision):
    require_connection(connection)
    config = Config('alembic.ini')
    config.attributes['connection'] = connection
    command.downgrade(config, revision)
