from src.modules.check_permission.service import StudentPermissionService
from src.modules.check_permission.depends import (
    get_current_user_with_target_permission,
    get_current_teacher_user,
)

__all__ = [
    "StudentPermissionService",
    "get_current_user_with_target_permission",
    "get_current_teacher_user",
]
