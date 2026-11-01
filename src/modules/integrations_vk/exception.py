from src.modules.base.exception import ServiceException


class IdentityError(ServiceException):
    def __init__(self, code: str, status: int = 409):
        self.code = code
        self.status = status
        super().__init__(code)
