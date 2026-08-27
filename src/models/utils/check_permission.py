from src.models.utils.exception import NotPermission


def check_permission(current_user_id: int, needed_user_id: int) -> None:
    """
    Если нет прав, то вызывает исключение
    :raise NotPermission:
    """
    if current_user_id != needed_user_id:
        raise NotPermission()