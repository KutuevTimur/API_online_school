from src.modules.base.exception import ServiceException


class StudentNotFound(ServiceException):
    pass


class StudentAlreadyExists(ServiceException):
    pass
