from src.modules.check_permission.exception import PermissionErrorService
from src.modules.users.models import Users, UserRole


class StudentPermissionService:

    @staticmethod
    def check_can_update(
        current_user: Users,
        target_user_id: int,
    ) -> None:
        """
        :exception PermissionErrorService: Если пользователь не является учителем или ``current_user.id`` != ``target_user_id``
        """
        if current_user.role in {
            UserRole.TEACHER,
        }:
            return

        if current_user.id == target_user_id:
            return

        raise PermissionErrorService()
