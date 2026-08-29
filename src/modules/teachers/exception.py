from src.modules.base.exception import ServiceException


class TeacherNotFound(ServiceException):
    pass


class TeacherAlreadyExists(ServiceException):
    pass
