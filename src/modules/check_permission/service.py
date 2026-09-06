from src.modules.check_permission.exception import PermissionErrorService
from src.modules.users.models import UserRole
from src.modules.users.models_dto import UserDTO


class StudentPermissionService:

    @staticmethod
    def check_role_and_id(
        current_user: UserDTO,
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
        current_user: UserDTO,
    ) -> None:
        """
        :exception PermissionErrorService: Если пользователь не является учителем
        """
        if current_user.role in {
            UserRole.TEACHER,
        }:
            return

        raise PermissionErrorService()

    @staticmethod
    def check_admin_password(
        provided_password: str,
        expected_password: str,
    ) -> None:
        """
        :exception PermissionErrorService: Если пароль администратора не совпадает
        """
        if provided_password != expected_password:
            raise PermissionErrorService()
