from src.models.base.exception import ServiceException


class StudentNotFound(ServiceException):
    pass


class StudentAlreadyExists(ServiceException):
    pass
