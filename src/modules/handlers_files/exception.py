from src.modules.base.exception import ServiceException

class HandlerFileException(ServiceException):
    """Базовое исключение для работы с файлами."""
    pass

class InvalidImageFormat(HandlerFileException):
    """Исключение при неподдерживаемом или неверном формате изображения."""
    pass

class ImageConversionError(HandlerFileException):
    """Исключение при ошибке конвертации изображения."""
    pass

class ImageCompressionError(HandlerFileException):
    """Исключение при ошибке сжатия изображения."""
    pass

class InvalidDocumentFormat(HandlerFileException):
    """Исключение при неподдерживаемом или неверном формате документа."""
    pass

class DocumentConversionError(HandlerFileException):
    """Исключение при ошибке конвертации документа."""
    pass
