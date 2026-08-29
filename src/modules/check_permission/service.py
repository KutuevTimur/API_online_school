from src.modules.check_permission.exception import PermissionErrorService
from src.modules.users.models import UserRole
from src.modules.users.models_dto import UsersDTO


class StudentPermissionService:

    @staticmethod
    def check_role_and_id(
        current_user: UsersDTO,
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

    @staticmethod
    def check_role(
        current_user: UsersDTO,
    ) -> None:
        """
        :exception PermissionErrorService: Если пользователь не является учителем
        """
        if current_user.role in {
            UserRole.TEACHER,
        }:
            return

        raise PermissionErrorService()