from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base.exception import ServiceException
from src.models.users.exception import UserAlreadyExit
from src.models.users.models_dto import UsersDTO, RegisterUserRequestDTO, CreateUserDTO
from src.models.users.repository import UsersRepository


class UsersService:

    def __init__(
        self,
        users_repo: UsersRepository,
        cr_context: CryptContext,
        session_db: AsyncSession,
    ):
        self.users_repo = users_repo
        self.cr_context = cr_context
        self.session_db = session_db

    def _get_hash_password(self, password: str) -> str:
        """Преобразует пароль в хеш
        :return: хэш пароля"""
        return self.cr_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Проверяет, совпадает ли пароль с хешем
        :param plain_password: простой пароль (qwerty)
        :param hashed_password: хэш пароля (gfdjkjvzvxccxa)
        :return: результат совпадения
        """
        return self.cr_context.verify(plain_password, hashed_password)

    async def get_user_by_username_or_email(self, username_or_email: str) -> UsersDTO | None:
        result = await self.users_repo.get_user_by_username_or_email(username_or_email)
        return UsersDTO.model_validate(result) if result else None

    async def get_user_by_id(self, user_id: int) -> UsersDTO | None:
        result = await self.users_repo.get_user_by_id(user_id)
        return UsersDTO.model_validate(result) if result else None

    async def get_user_by_email(self, email: str) -> UsersDTO | None:
        result = await self.users_repo.get_user_by_email(email)
        return UsersDTO.model_validate(result) if result else None

    async def create_user(
        self,
        new_user: RegisterUserRequestDTO
    ) -> UsersDTO:
        """
        :raises UserAlreadyExit:
        """
        if await self.get_user_by_username_or_email(new_user.email):
            raise UserAlreadyExit()

        hashed_password = self._get_hash_password(new_user.password)

        try:
            result = await self.users_repo.add_user(
                data=CreateUserDTO(
                    email=new_user.email,
                    username=new_user.username,
                    hashed_password=hashed_password,
                )
            )
            await self.session_db.commit()
            await self.session_db.refresh(result)
        except Exception as e:
            if 'email' in str(e).lower() or 'duplicate key' in str(e).lower():
                raise UserAlreadyExit()
            else:
                raise ServiceException() from e

        return UsersDTO.model_validate(result)



