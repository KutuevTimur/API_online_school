from fastapi import Request, Depends

from src.core.config import Config
from src.modules.depends import get_config
from src.modules.handlers_files.compression_images import CompressionImages
from src.modules.handlers_files.converter_images import HandlerImages
from src.modules.path_builder import PathBuilder
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository
from src.core.database.database import get_db
from src.modules.users.repository import UsersRepository
from src.modules.users.service import UsersService


def get_user_service(
    request: Request,
    session = Depends(get_db),
    config: Config = Depends(get_config),
) -> UsersService:
    return UsersService(
        users_repo=UsersRepository(session=session),
        teacher_repo=TeacherRepository(session=session),
        student_repo=StudentRepository(session=session),
        cr_context=request.app.state.cr_context,
        path_builder=PathBuilder(config=config),
        handler_images=HandlerImages(config=config),
        compression_images=CompressionImages(config=config),
        session_db=session,
    )
