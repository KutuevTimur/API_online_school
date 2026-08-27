from src.models.base.exception import ServiceException


class UserNotFound(ServiceException):
    pass


class UserAlreadyExit(ServiceException):
    pass

