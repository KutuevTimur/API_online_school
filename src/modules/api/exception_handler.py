from fastapi import FastAPI
from starlette.responses import JSONResponse

from src.modules.courses.exception import CourseAlreadyExists
from src.modules.users.exception import InvalidRole
from src.modules.auth.exception import InvalidCredentials, InvalidJWTToken
from src.modules.base.exception import ServiceException, NoDataForUpdate, NotFoundData
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.lesson_students.exception import LessonStudentAlreadyExists
from src.modules.lectures.exception import LectureAlreadyExists
from src.modules.homeworks.exception import HomeworkNotFound
from src.modules.lessons.exception import LessonNotFound
from src.modules.handlers_files.exception import (
    InvalidImageFormat,
    ImageConversionError,
    ImageCompressionError,
    InvalidDocumentFormat,
    DocumentConversionError,
)


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(LessonStudentAlreadyExists)
    async def lesson_student_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc) or "Student is already in this lesson"})

    @app.exception_handler(LectureAlreadyExists)
    async def lecture_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc) or "Lecture already exists"})

    @app.exception_handler(HomeworkNotFound)
    async def homework_not_found_handler(request, exc):
        return JSONResponse(status_code=404, content={"detail": str(exc) or "Homework not found"})

    @app.exception_handler(LessonNotFound)
    async def lesson_not_found_handler(request, exc):
        return JSONResponse(status_code=404, content={"detail": str(exc) or "Lesson not found"})

    @app.exception_handler(InvalidDocumentFormat)
    async def invalid_document_format_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc) or "Invalid document format"})

    @app.exception_handler(DocumentConversionError)
    async def document_conversion_error_handler(request, exc):
        return JSONResponse(status_code=500, content={"detail": str(exc) or "Document conversion error"})

    @app.exception_handler(ServiceException)
    async def service_handler(request, exc):
        return JSONResponse(status_code=500, content={"detail": "Server Error"})

    @app.exception_handler(NoDataForUpdate)
    async def service_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": "Did not transmit data"})

    @app.exception_handler(InvalidRole)
    async def service_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": "Invalid role"})

    @app.exception_handler(InvalidJWTToken)
    async def service_handler(request, exc):
        return JSONResponse(status_code=401, content={"detail": "Invalid JWT token"})

    @app.exception_handler(InvalidCredentials)
    async def service_handler(request, exc):
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})

    @app.exception_handler(NotFoundData)
    async def service_handler(request, exc):
        return JSONResponse(status_code=404, content={"detail": "Not found data"})

    @app.exception_handler(PermissionErrorService)
    async def service_handler(request, exc):
        return JSONResponse(status_code=403, content={"detail": "Not permission"})

    @app.exception_handler(CourseAlreadyExists)
    async def course_already_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc) or "Course already exists"})

    @app.exception_handler(InvalidImageFormat)
    async def invalid_image_format_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc) or "Invalid image format"})

    @app.exception_handler(ImageConversionError)
    async def image_conversion_error_handler(request, exc):
        return JSONResponse(status_code=500, content={"detail": "Image conversion error"})

    @app.exception_handler(ImageCompressionError)
    async def image_compression_error_handler(request, exc):
        return JSONResponse(status_code=500, content={"detail": "Image compression error"})
