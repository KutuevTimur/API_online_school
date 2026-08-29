import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from helpers import test_crypto_context
from src.modules.users.repository import UsersRepository
from src.modules.users.service import UsersService


@pytest_asyncio.fixture(scope="function")
async def user_service_fixture(session_db: AsyncSession) -> UsersService:
    return UsersService(
        users_repo=UsersRepository(session=session_db),
        cr_context=test_crypto_context,
        session_db=session_db,
    )

