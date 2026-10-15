from src.modules.base.exception import NotFoundData


class LessonNotFound(NotFoundData):
    pass


from src.modules.base.exception import ServiceException


class InvalidLessonRequest(ServiceException):
    pass
