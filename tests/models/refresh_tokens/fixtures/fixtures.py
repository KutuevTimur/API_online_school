import pytest_asyncio

from src.models.refresh_tokens.models_dto import RefreshTokenDTO
from src.core.config import Config
from tests.helpers import test_crypto_context
from tests.models.refresh_tokens.fixtures.factory import create_refresh_token_factory
from tests.models.refresh_tokens.fixtures.models_dto import CreateRefreshTokenFixtureDTO


@pytest_asyncio.fixture(scope="function")
async def create_refresh_token_fixture(
    config_fix: Config,
    not_open_session_db
):
    """
    :return: Возвращает функцию -> функция возвращает `UsersDTO` и `access_token`
    """

    async def _factory(
        new_refresh_token: CreateRefreshTokenFixtureDTO,
    ) -> RefreshTokenDTO:
        async with not_open_session_db() as session:
            token = await create_refresh_token_factory(
                session_db=session,
                crypto_context=test_crypto_context,
                new_refresh_token=new_refresh_token,
            )

            return token

    return _factory