import uuid
from pathlib import Path
from typing import Optional

from fastapi import UploadFile
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.handlers_files.compression_images import CompressionImages
from src.modules.handlers_files.converter_images import HandlerImages
from src.modules.path_builder import PathBuilder
from src.modules.students.models_dto import CreateStudentDTO
from src.modules.students.repository import StudentRepository
from src.modules.teachers.models_dto import CreateTeacherDTO
from src.modules.teachers.repository import TeacherRepository
from src.modules.users.exception import UserAlreadyExit, InvalidRole
from src.modules.users.models import UserRole
from src.modules.users.models_dto import UsersDTO, RegisterUserRequestDTO, CreateUserDTO
from src.modules.users.repository import UsersRepository


class UsersService:

    def __init__(
        self,
        users_repo: UsersRepository,
        teacher_repo: TeacherRepository,
        student_repo: StudentRepository,
        cr_context: CryptContext,
        path_builder: PathBuilder,
        handler_images: HandlerImages,
        compression_images: CompressionImages,
        session_db: AsyncSession,
    ):
        self.users_repo = users_repo
        self.teacher_repo = teacher_repo
        self.student_repo = student_repo
        self.cr_context = cr_context
        self.path_builder = path_builder
        self.handler_images = handler_images
        self.compression_images = compression_images
        self.session_db = session_db

    def _get_hash_password(self, password: str) -> str:
        """Преобразует пароль в хеш
        :return: хэш пароля"""
        return self.cr_context.hash(password)

    async def _create_avatar(self, user_id: int, avatar: UploadFile) -> str:
        """
        Преобразовывает в формат .webp и сжимает фото до 512x512.
        :return: Путь к аватарке
        :raises InvalidImageFormat: Если расширение или формат файла недопустимы / повреждены.
        :raises ImageConversionError: При ошибке в процессе конвертации / сжатия / сохранения.
        """
        temp_webp = Path()
        result_file_path = Path()
        try:
            temp_webp = self.path_builder.get_temp() / Path(uuid.uuid4().hex)
            temp_webp = await self.handler_images.convert_to_webp(photo=avatar, dest=temp_webp)

            result_file_path = self.path_builder.get_avatar_user(user_id)
            result_file_path = await self.compression_images.compress_webp(file=temp_webp, dest=result_file_path)
        except Exception:
            temp_webp.unlink(missing_ok=True)
            result_file_path.unlink(missing_ok=True)
            raise

        temp_webp.unlink(missing_ok=True)
        return str(result_file_path)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Проверяет, совпадает ли пароль с хешем
        :param plain_password: простой пароль (qwerty)
        :param hashed_password: хэш пароля (gfdjkjvzvxccxa)
        :return: результат совпадения
        """
        return self.cr_context.verify(plain_password, hashed_password)

    async def get_user_by_username_or_email(self, username_or_email: str) -> UsersDTO | None:
        result = await self.users_repo.get_user_by_username_or_email(username_or_email)
        return UsersDTO.model_validate(result) if result else None

    async def get_user_by_id(self, user_id: int) -> UsersDTO | None:
        result = await self.users_repo.get_user_by_id(user_id)
        return UsersDTO.model_validate(result) if result else None

    async def get_user_by_email(self, email: str) -> UsersDTO | None:
        result = await self.users_repo.get_user_by_email(email)
        return UsersDTO.model_validate(result) if result else None

    async def create_user(
        self,
        new_user: RegisterUserRequestDTO,
        avatar: Optional[UploadFile] = None
    ) -> UsersDTO:
        """
        :raises UserAlreadyExit:
        :raises InvalidImageFormat: Если расширение или формат файла недопустимы / повреждены.
        :raises ImageConversionError: При ошибке в процессе конвертации / сжатия / сохранения.
        """
        if await self.get_user_by_username_or_email(new_user.email):
            raise UserAlreadyExit()

        hashed_password = self._get_hash_password(new_user.password)

        try:
            user_orm = await self.users_repo.add_user(
                data=CreateUserDTO(
                    email=new_user.email,
                    username=new_user.username,
                    hashed_password=hashed_password,
                    role=new_user.role,
                )
            )

            await self.session_db.flush()

            avatar_path = await self._create_avatar(user_id=user_orm.id, avatar=avatar) if avatar else None

            if new_user.role == UserRole.TEACHER:
                teacher_orm = await self.teacher_repo.add_teacher(
                    CreateTeacherDTO(
                        user_id=user_orm.id,
                        first_name=new_user.first_name,
                        last_name=new_user.last_name,
                        middle_name=new_user.middle_name,
                        avatar_path=avatar_path,
                        description=new_user.description,
                    )
                )
            elif new_user.role == UserRole.STUDENT:
                student_orm = await self.student_repo.add_student(
                    CreateStudentDTO(
                        user_id=user_orm.id,
                        first_name=new_user.first_name,
                        last_name=new_user.last_name,
                        middle_name=new_user.middle_name,
                        avatar_path=avatar_path,
                    )
                )
            else:
                raise InvalidRole()

            await self.session_db.commit()
        except Exception as e:
            if 'email' in str(e).lower() or 'duplicate key' in str(e).lower():
                raise UserAlreadyExit()
            else:
                raise

        return UsersDTO.model_validate(user_orm)
