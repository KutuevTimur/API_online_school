from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.database.database import get_db

from src.modules.auth.depends import get_current_user
from src.modules.check_permission.service import StudentPermissionService
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.users.models import UserRole
from src.modules.users.models_dto import UserDTO


async def get_current_user_with_target_permission(
    user_id: int,
    session: AsyncSession = Depends(get_db),
    current_user: UserDTO = Depends(get_current_user),
) -> UserDTO:
    """
    Проверяет, имеет ли пользователь доступ к ресурсам, связанным с target_user_id.
    :raises PermissionErrorService:
    """
    from src.modules.check_permission.service import ObjectPermissionService
    await ObjectPermissionService(session).require(current_user.id, "profile", user_id, write=True)
    return current_user


async def get_current_admin_user(current_user: UserDTO = Depends(get_current_user)) -> UserDTO:
    if current_user.role != UserRole.ADMIN:
        raise PermissionErrorService()
    return current_user


async def get_account_creator(current_user: UserDTO = Depends(get_current_user)) -> UserDTO:
    if current_user.role not in {UserRole.ADMIN, UserRole.TEACHER}:
        raise PermissionErrorService()
    return current_user


async def get_current_teacher_user(
    current_user: UserDTO = Depends(get_current_user),
) -> UserDTO:
    """
    Проверяет, является ли пользователь учителем.
    :raises PermissionErrorService:
    """
    StudentPermissionService.check_role(current_user=current_user)
    return current_user


async def get_current_student_user(
    current_user: UserDTO = Depends(get_current_user),
) -> UserDTO:
    """
    Проверяет, является ли пользователь учеником.
    :raises PermissionErrorService:
    """
    if current_user.role != UserRole.STUDENT:
        raise PermissionErrorService()
    return current_user
