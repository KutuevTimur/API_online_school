from src.modules.base.exception import ServiceException, NotFoundData

class LectureAlreadyExists(ServiceException):
    pass

class LectureNotFound(NotFoundData):
    pass


class LectureLimitReached(ServiceException):
    """A lesson recipient supports at most four material files."""
    pass
