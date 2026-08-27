from fastapi import Request, Depends

from src.core.database.database import get_db
from src.models.users.repository import UsersRepository
from src.models.users.service import UsersService


def get_user_service(
    request: Request,
    session = Depends(get_db),
) -> UsersService:
    return UsersService(
        users_repo=UsersRepository(session=session),
        cr_context=request.app.state.cr_context,
        session_db=session,
    )