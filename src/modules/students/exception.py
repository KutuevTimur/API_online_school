from src.modules.base.exception import ServiceException, NotFoundData


class StudentNotFound(NotFoundData):
    pass


class StudentAlreadyExists(ServiceException):
    pass
