from src.models.base.exception import ServiceException


class TeacherNotFound(ServiceException):
    pass


class TeacherAlreadyExists(ServiceException):
    pass
