from sqlalchemy import select, text
from src.modules.users.repository import UsersRepository
from src.modules.users.models import User, UserRole


class BootstrapRepository(UsersRepository):
    async def lock(self) -> None:
        await self.session.execute(text("SELECT pg_advisory_xact_lock(5930505)"))

    async def has_admin(self) -> bool:
        return (await self.session.execute(select(User.id).where(User.role == UserRole.ADMIN).limit(1))).scalar_one_or_none() is not None
