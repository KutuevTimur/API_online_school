from tests.fixturs.fixturs_db import session_db, not_open_session_db
from tests.fixturs.replace_services import user_service_fixture, courses_service_fixture
from tests.fixturs.fixtures import app_fastapi, config_fix, client_for_tests, \
    lifespan_for_tests, cleaning_paths_fix

from tests.modules.users.fixtures import create_user_fixture
from tests.modules.refresh_tokens.fixtures import create_refresh_token_fixture

__all__ = [
    "lifespan_for_tests",
    "app_fastapi",
    "not_open_session_db",
    "client_for_tests",

    # БД фикстуры
    "config_fix",
    "cleaning_paths_fix",
    "session_db",

    # сервисы
    "user_service_fixture",
    "courses_service_fixture",

    # из моделей
    "create_user_fixture",
    "create_refresh_token_fixture",
]
