from src.modules.base.exception import ServiceException, NotFoundData
from src.modules.check_permission.exception import PermissionErrorService


class EnrollmentExistsException(ServiceException):
    pass


class EnrollmentNotFoundException(NotFoundData):
    pass


class CourseAccessDeniedException(PermissionErrorService):
    pass
