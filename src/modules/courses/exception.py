from src.modules.base.exception import NotFoundData, ServiceException


class CourseNotFound(NotFoundData):
    pass


class CourseAvatarNotFound(NotFoundData):
    pass


class CourseAlreadyExists(ServiceException):
    pass
