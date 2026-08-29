from src.modules.base.exception import ServiceException


class HandlerFileException(ServiceException):
    """Базовое исключение для операций с файлами."""
    pass


class InvalidImageFormat(HandlerFileException):
    """Исключение при недопустимом или неподдерживаемом формате изображения."""
    pass


class ImageConversionError(HandlerFileException):
    """Исключение при ошибке конвертации изображения."""
    pass


class ImageCompressionError(HandlerFileException):
    """Исключение при ошибке сжатия изображения."""
    pass
