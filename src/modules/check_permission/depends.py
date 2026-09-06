from fastapi import Depends

from src.modules.auth.depends import get_current_user
from src.modules.check_permission.service import StudentPermissionService
from src.modules.users.models_dto import UserDTO


async def get_current_user_with_target_permission(
    user_id: int,
    current_user: UserDTO = Depends(get_current_user),
) -> UserDTO:
    """
    Проверяет, что текущий пользователь имеет доступ к target_user_id (он сам или учитель),
    и возвращает current_user.
    :raises PermissionErrorService: Если нет прав доступа
    """
    StudentPermissionService.check_role_and_id(
        current_user=current_user,
        target_user_id=user_id,
    )
    return current_user


async def get_current_teacher_user(
    current_user: UserDTO = Depends(get_current_user),
) -> UserDTO:
    """
    Проверяет, что текущий пользователь является преподавателем, и возвращает его.
    :raises PermissionErrorService: Если пользователь не является учителем
    """
    StudentPermissionService.check_role(current_user=current_user)
    return current_user
