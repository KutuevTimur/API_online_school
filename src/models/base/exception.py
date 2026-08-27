

class ServiceException(Exception):
    pass


class RepositoryException(Exception):
    pass


class NotFoundData(Exception):
    pass


class NoDataForUpdate(RepositoryException):
    pass

