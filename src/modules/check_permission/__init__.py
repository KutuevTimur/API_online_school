from src.modules.check_permission.depends import (
    get_current_user_with_target_permission,
    get_current_teacher_user,
    get_current_student_user,
)
from src.modules.check_permission.service import StudentPermissionService

__all__ = [
    "get_current_user_with_target_permission",
    "get_current_teacher_user",
    "get_current_student_user",
    "StudentPermissionService",
]
