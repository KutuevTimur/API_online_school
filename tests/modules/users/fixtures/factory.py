from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from helpers.functions import random_string
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from src.modules.students.models import Student
from src.modules.teachers.models import Teacher
from src.modules.users.models import User, UserRole
from src.modules.users.models_dto import UserDTO


def _get_hash_password(crypto_context: CryptContext, password: str) -> str:
    """Преобразует пароль в хеш
    :return: хэш пароля"""
    return crypto_context.hash(password)


async def create_user_factory(
    session_db: AsyncSession,
    crypto_context: CryptContext,
    new_user: CreateUserFixtureDTO = CreateUserFixtureDTO(),
) -> UserDTO:
    user = User(
        email=random_string() + "@mail.com" if new_user.email is None else new_user.email,
        username=random_string() if new_user.username is None else new_user.username,
        hashed_password=_get_hash_password(
            crypto_context=crypto_context,
            password=random_string() if new_user.password is None else new_user.password
        ),
        role=new_user.role,
    )
    session_db.add(user)
    await session_db.commit()
    await session_db.refresh(user)

    if new_user.role == UserRole.TEACHER:
        teacher = Teacher(
            user_id=user.id,
            first_name=user.username,
            last_name="Teacher",
        )
        session_db.add(teacher)
        await session_db.commit()
    elif new_user.role == UserRole.STUDENT:
        student = Student(
            user_id=user.id,
            first_name=user.username,
            last_name="Student",
        )
        session_db.add(student)
        await session_db.commit()

    return UserDTO.model_validate(user)
