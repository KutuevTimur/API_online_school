from typing import List, Tuple

from sqlalchemy import select, or_, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.users.models import User, UserRole
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
        result_db = await self.session.execute(
            select(User)
            .where(User.id == user_id)
            .options(
                selectinload(User.teacher),
                selectinload(User.student),
            )
        )
        return result_db.scalar_one_or_none()

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

    async def get_users_by_role(
        self,
        role: UserRole,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[int, List[User]]:
        """Получить пользователей по роли с связанных профилем"""
        from sqlalchemy import func
        count_stmt = select(func.count()).select_from(User).where(User.role == role)
        total_count = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = (
            select(User)
            .where(User.role == role)
            .options(
                selectinload(User.teacher), 
                selectinload(User.student)
            )
            .limit(limit)
            .offset(offset)
            .order_by(User.id.desc())
        )
        result_db = await self.session.execute(stmt)
        users = list(result_db.scalars().all())
        return total_count, users

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
