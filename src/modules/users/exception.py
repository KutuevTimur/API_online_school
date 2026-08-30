from src.modules.base.exception import ServiceException, NotFoundData


class UserNotFound(NotFoundData):
    pass


class AvatarNotFound(NotFoundData):
    pass


class InvalidRole(ServiceException):
    pass


class UserAlreadyExit(ServiceException):
    pass

