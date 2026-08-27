from datetime import datetime, UTC, timedelta
from typing import Tuple

import pytest_asyncio
from jose import jwt

from tests.helpers import test_crypto_context
from tests.models.users.fixtures.models_dto import CreateUserFixtureDTO
from src.core.config import Config
from src.models.users.models_dto import UsersDTO
from tests.models.users.fixtures.factory import create_user_factory


def create_accesses_token(user_id: int, conf: Config) -> str:
    to_encode = {"sub": str(user_id)}.copy()

    # Установка времени истечения токена
    expire = datetime.now(UTC) + timedelta(minutes=conf.tokens.access_token_expire_minutes)
    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        conf.env.secret_key,
        algorithm=conf.tokens.algorithm
    )


@pytest_asyncio.fixture(scope="function")
async def create_user_fixture(
    config_fix: Config,
    not_open_session_db
):
    """
    :return: Возвращает функцию -> функция возвращает `UsersDTO` и `access_token`
    """

    async def _factory(
        new_user: CreateUserFixtureDTO = CreateUserFixtureDTO(),
    ) -> Tuple[UsersDTO, str]:
        async with not_open_session_db() as session:
            user = await create_user_factory(
                session_db=session,
                crypto_context=test_crypto_context,
                new_user=new_user,
            )

            access_token = create_accesses_token(user.id, config_fix)

            return user, access_token

    return _factory