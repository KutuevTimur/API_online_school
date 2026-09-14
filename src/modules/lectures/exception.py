from src.modules.base.exception import ServiceException, NotFoundData

class LectureAlreadyExists(ServiceException):
    pass

class LectureNotFound(NotFoundData):
    pass
