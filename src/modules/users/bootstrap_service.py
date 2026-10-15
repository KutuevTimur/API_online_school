from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.users.repository import UsersRepository
from src.modules.users.models_dto import CreateUserDTO
from src.modules.users.models import UserRole
from src.modules.users.bootstrap_dto import BootstrapInput


async def bootstrap_admin(session: AsyncSession, data: BootstrapInput, crypto: CryptContext) -> bool:
    """Serialize concurrent bootstraps and refuse creation if any admin exists."""
    from src.modules.users.bootstrap_repository import BootstrapRepository
    try:
        repo = BootstrapRepository(session)
        await repo.lock()
        if await repo.has_admin():
            await session.rollback()
            return False
        await UsersRepository(session).add_user(CreateUserDTO(
            username=data.username, email=str(data.email),
            hashed_password=crypto.hash(data.password), role=UserRole.ADMIN))
        await session.commit()
        return True
    except Exception:
        await session.rollback()
        raise
