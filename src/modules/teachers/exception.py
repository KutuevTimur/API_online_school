from src.modules.base.exception import ServiceException, NotFoundData


class TeacherNotFound(NotFoundData):
    pass


class TeacherAlreadyExists(ServiceException):
    pass
