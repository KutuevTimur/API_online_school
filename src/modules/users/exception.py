from src.modules.base.exception import ServiceException


class UserNotFound(ServiceException):
    pass


class UserAlreadyExit(ServiceException):
    pass

