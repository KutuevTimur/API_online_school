from src.modules.base.exception import NotFoundData
from src.modules.check_permission.exception import PermissionErrorService


class HomeworkSubmissionNotFound(NotFoundData):
    pass


class HomeworkSubmissionFileNotFound(NotFoundData):
    pass


class HomeworkSubmissionNotEditable(PermissionErrorService):
    def __init__(self, message: str = "Homework submission cannot be edited because it is already CHECKED"):
        super().__init__(message)


from src.modules.base.exception import ServiceException


class SubmissionConflict(ServiceException):
    pass


class EmptySubmission(ServiceException):
    pass
