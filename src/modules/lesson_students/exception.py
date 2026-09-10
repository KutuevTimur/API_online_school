from src.modules.base.exception import ServiceException, NotFoundData

class LessonStudentAlreadyExists(ServiceException):
    pass

class LessonStudentNotFound(NotFoundData):
    pass
