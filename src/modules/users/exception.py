from src.modules.base.exception import ServiceException, NotFoundData


class UserNotFound(NotFoundData):
    pass


class UserAlreadyExit(ServiceException):
    pass

