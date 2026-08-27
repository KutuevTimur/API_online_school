from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from helpers.functions import random_string
from tests.models.users.fixtures.models_dto import CreateUserFixtureDTO
from src.models.users.models import Users
from src.models.users.models_dto import UsersDTO


def _get_hash_password(crypto_context: CryptContext, password: str) -> str:
    """Преобразует пароль в хеш
    :return: хэш пароля"""
    return crypto_context.hash(password)


async def create_user_factory(
    session_db: AsyncSession,
    crypto_context: CryptContext,
    new_user: CreateUserFixtureDTO = CreateUserFixtureDTO(),
) -> UsersDTO:
    user = Users(
        email=random_string() + "@mail.com" if new_user.email is None else new_user.email,
        username=random_string() if new_user.username is None else new_user.username,
        hashed_password=_get_hash_password(
            crypto_context=crypto_context,
            password=random_string() if new_user.password is None else new_user.password
        )
    )
    session_db.add(user)
    await session_db.commit()
    await session_db.refresh(user)

    return UsersDTO.model_validate(user)

