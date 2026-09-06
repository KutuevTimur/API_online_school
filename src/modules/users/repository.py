from sqlalchemy import select, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import BaseRepository
from src.modules.users.models import User
from src.modules.users.models_dto import CreateUserDTO


class UsersRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=User)

    async def add_user(
        self,
        data: CreateUserDTO,
    ) -> User:
        return self.add(data)

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.get_by_id(User, user_id)

    async def get_user_by_username_or_email(self, username_or_email: str) -> User | None:
        result_db = await self.session.execute(
            select(User)
            .where(
                or_(
                    User.username == username_or_email,
                    User.email == username_or_email
                )
            )
        )
        return result_db.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        result_db = await self.session.execute(select(User).where(User.email == email))
        return result_db.scalar_one_or_none()

    async def update_user(
        self,
        user_id: int,
        values: dict,
    ) -> User | None:
        result_db = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(**values)
            .returning(User)
        )
        return result_db.scalar_one_or_none()
