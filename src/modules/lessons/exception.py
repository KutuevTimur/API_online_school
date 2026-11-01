from src.modules.base.exception import NotFoundData


class LessonNotFound(NotFoundData):
    pass


from src.modules.base.exception import ServiceException


class InvalidLessonRequest(ServiceException):
    pass


class RegularPreviewChanged(ServiceException):
    def __init__(self, preview: dict) -> None:
        super().__init__("Расписание изменилось. Проверьте новый предпросмотр и подтвердите ещё раз.")
        self.preview = preview
