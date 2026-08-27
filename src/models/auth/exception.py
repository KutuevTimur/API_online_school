from src.models.base.exception import ServiceException


class InvalidJWTToken(ServiceException):
    pass

class InvalidCredentials(ServiceException):
    pass