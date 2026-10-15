from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.base.exception import ServiceException


if TYPE_CHECKING:
    from src.modules.users.models_dto import UserDTO


class InvalidJWTToken(ServiceException):
    pass


class InvalidCredentials(ServiceException):
    pass


def require_active_user(user: UserDTO | None) -> UserDTO:
    """Use the same authorization failure for missing and disabled accounts."""
    if user is None or not user.is_active or not user.is_activated:
        raise InvalidCredentials()
    return user
