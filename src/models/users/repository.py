from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base.database_model import BaseRepository
from src.models.users.models import Users
from src.models.users.models_dto import CreateUserDTO


class UsersRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Users)

    async def add_user(
        self,
        data: CreateUserDTO,
    ) -> Users:
        return self.add(data)

    async def get_user_by_id(self, user_id: int) -> Users:
        return await self.get_by_id(Users, user_id)

    async def get_user_by_username_or_email(self, username_or_email: str) -> Users | None:
        result_db = await self.session.execute(
            select(Users)
            .where(
                or_(
                    Users.username == username_or_email,
                    Users.email == username_or_email
                )
            )
        )
        return result_db.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Users | None:
        result_db = await self.session.execute(select(Users).where(Users.email == email))
        return result_db.scalar_one_or_none()



