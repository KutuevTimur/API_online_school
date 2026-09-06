import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.exception import NotFoundData
from src.modules.handlers_files.compression_images import CompressionImages
from src.modules.handlers_files.converter_images import HandlerImages
from src.modules.path_builder import PathBuilder
from src.modules.students.models_dto import CreateStudentDTO, UpdateStudentDTO, StudentsDTO
from src.modules.students.repository import StudentRepository
from src.modules.students.service import StudentService
from src.modules.teachers.repository import TeacherRepository
from src.modules.teachers.service import TeacherService
from src.modules.teachers.models_dto import CreateTeacherDTO, UpdateTeacherDTO, TeachersDTO
from src.modules.users.exception import UserAlreadyExit, InvalidRole, AvatarNotFound
from src.modules.users.models import UserRole
from src.modules.users.models_dto import (
    UserDTO,
    RegisterUserRequestDTO,
    CreateUserDTO,
    UserAvatarResponseDTO,
    UpdateUserDataRequestDTO,
)
from src.modules.users.repository import UsersRepository


class UsersService:

    def __init__(
        self,
        users_repo: UsersRepository,
        teacher_repo: TeacherRepository,
        teacher_service: TeacherService,
        student_repo: StudentRepository,
        student_service: StudentService,
        cr_context: CryptContext,
        path_builder: PathBuilder,
        handler_images: HandlerImages,
        compression_images: CompressionImages,
        session_db: AsyncSession,
    ):
        self.users_repo = users_repo
        self.teacher_repo = teacher_repo
        self.teacher_service = teacher_service
        self.student_repo = student_repo
        self.student_service = student_service
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
        temp_webp: Path | None = None
        result_file_path: Path | None = None
        try:
            temp_webp = self.path_builder.get_temp() / Path(f"{uuid.uuid4().hex}.webp")
            temp_webp = await self.handler_images.convert_to_webp(photo=avatar, dest=temp_webp)

            result_file_path = self.path_builder.get_avatar_user(user_id)
            result_file_path = await self.compression_images.compress_webp(file=temp_webp, dest=result_file_path)
        except Exception:
            if temp_webp and temp_webp.is_file():
                temp_webp.unlink(missing_ok=True)
            if result_file_path and result_file_path.is_file():
                result_file_path.unlink(missing_ok=True)
            raise
        finally:
            if temp_webp and temp_webp.is_file():
                temp_webp.unlink(missing_ok=True)

        return str(result_file_path)

    def delete_avatar(self, user_id: int) -> None:
        """
        :raises AvatarNotFound: Если аватар не найден
        """
        avatar_path = self.path_builder.get_avatar_user(user_id)
        if avatar_path.is_file():
            shutil.rmtree(avatar_path.parent)
        else:
            raise AvatarNotFound()

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Проверяет, совпадает ли пароль с хешем
        :param plain_password: простой пароль (qwerty)
        :param hashed_password: хэш пароля (gfdjkjvzvxccxa)
        :return: результат совпадения
        """
        return self.cr_context.verify(plain_password, hashed_password)

    async def get_user_by_username_or_email(self, username_or_email: str) -> UserDTO | None:
        result = await self.users_repo.get_user_by_username_or_email(username_or_email)
        return UserDTO.model_validate(result) if result else None

    async def get_user_by_id(self, user_id: int) -> UserDTO | None:
        result = await self.users_repo.get_user_by_id(user_id)
        return UserDTO.model_validate(result) if result else None

    async def get_user_by_email(self, email: str) -> UserDTO | None:
        result = await self.users_repo.get_user_by_email(email)
        return UserDTO.model_validate(result) if result else None

    async def create_user(
        self,
        new_user: RegisterUserRequestDTO,
    ) -> UserDTO:
        """
        Создает нового пользователя (учителя или ученика).
        :raises UserAlreadyExit: Если пользователь с таким email/username уже существует.
        :raises InvalidRole: Если роль недопустима.
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

            if new_user.role == UserRole.TEACHER:
                await self.teacher_repo.add_teacher(
                    CreateTeacherDTO(
                        user_id=user_orm.id,
                        first_name=new_user.first_name,
                        last_name=new_user.last_name,
                        middle_name=new_user.middle_name,
                        description=new_user.description,
                    )
                )
            elif new_user.role == UserRole.STUDENT:
                await self.student_repo.add_student(
                    CreateStudentDTO(
                        user_id=user_orm.id,
                        first_name=new_user.first_name,
                        last_name=new_user.last_name,
                        middle_name=new_user.middle_name,
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

        return UserDTO.model_validate(user_orm)

    async def update_avatar(
        self,
        user_id: int,
        avatar: UploadFile,
    ) -> UserAvatarResponseDTO:
        """
        Обновляет аватарку пользователя.
        :param user_id: ID пользователя, которому обновляется аватарка
        :param avatar: Загружаемый файл
        :return: UserAvatarResponseDTO с путем к аватарке
        :raises NotFoundData: Если пользователь не найден
        :raises InvalidRole: Если роль пользователя неизвестна
        :raises InvalidImageFormat: Если формат файла недопустим / поврежден
        :raises ImageConversionError: При ошибке конвертации
        :raises ImageCompressionError: При ошибке сжатия
        """
        user = await self.users_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundData()

        try:
            self.delete_avatar(user_id=user_id)
        except AvatarNotFound:
            pass

        avatar_path = await self._create_avatar(user_id=user_id, avatar=avatar)

        if user.role == UserRole.TEACHER:
            await self.teacher_service.update_teacher_by_user_id(
                user_id=user_id,
                data=UpdateTeacherDTO(
                    avatar_path=avatar_path,
                )
            )
        elif user.role == UserRole.STUDENT:
            await self.student_service.update_student_by_user_id(
                user_id=user_id,
                data=UpdateStudentDTO(
                    avatar_path=avatar_path,
                )
            )
        else:
            raise InvalidRole()

        return UserAvatarResponseDTO(avatar_path=avatar_path)

    async def update_user(
        self,
        user_id: int,
        data: UpdateUserDataRequestDTO,
    ) -> TeachersDTO | StudentsDTO:
        """
        Обновляет данные профиля пользователя (учителя или ученика) и аккаунта по user_id.
        :param user_id: ID пользователя
        :param data: Данные для обновления
        :return: TeachersDTO или StudentsDTO
        :raises NotFoundData: Если пользователь не найден
        :raises UserAlreadyExit: Если email или username уже заняты другим пользователем
        :raises InvalidRole: Если роль пользователя неизвестна
        """
        user = await self.users_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundData()

        # Обновление данных аккаунта (таблица User)
        user_account_dto = data.to_user_account_dto()
        user_values = user_account_dto.model_dump(exclude_unset=True, exclude_none=True)

        if user_values:
            if user_account_dto.email:
                existing_by_email = await self.users_repo.get_user_by_email(user_account_dto.email)
                if existing_by_email and existing_by_email.id != user_id:
                    raise UserAlreadyExit()
            if user_account_dto.username:
                existing_by_username = await self.users_repo.get_user_by_username_or_email(user_account_dto.username)
                if existing_by_username and existing_by_username.id != user_id:
                    raise UserAlreadyExit()

            await self.users_repo.update_user(user_id=user_id, values=user_values)

        # Обновление данных профиля (таблицы Teacher / Student)
        if user.role == UserRole.TEACHER:
            teacher_dto = data.to_teacher_dto()
            profile_values = teacher_dto.model_dump(exclude_unset=True, exclude_none=True)
            if profile_values:
                teacher = await self.teacher_repo.update_teacher_by_user_id(
                    user_id=user_id,
                    values=profile_values,
                )
            else:
                teacher = await self.teacher_repo.get_teacher_by_user_id(user_id=user_id)

            if not teacher:
                raise NotFoundData()
            await self.session_db.commit()
            await self.session_db.refresh(teacher)
            return TeachersDTO.model_validate(teacher)

        elif user.role == UserRole.STUDENT:
            student_dto = data.to_student_dto()
            profile_values = student_dto.model_dump(exclude_unset=True, exclude_none=True)
            if profile_values:
                student = await self.student_repo.update_student_by_user_id(
                    user_id=user_id,
                    values=profile_values,
                )
            else:
                student = await self.student_repo.get_student_by_user_id(user_id=user_id)

            if not student:
                raise NotFoundData()
            await self.session_db.commit()
            await self.session_db.refresh(student)
            return StudentsDTO.model_validate(student)

        else:
            raise InvalidRole()

    async def change_password(
        self,
        user_id: int,
        new_password: str,
    ) -> UserDTO:
        """
        Изменяет пароль пользователя по user_id.
        :param user_id: ID пользователя
        :param new_password: Новый пароль
        :return: UserDTO обновленного пользователя
        :raises NotFoundData: Если пользователь не найден
        """
        user = await self.users_repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundData()

        hashed_password = self._get_hash_password(new_password)
        updated_user = await self.users_repo.update_user(
            user_id=user_id,
            values={"hashed_password": hashed_password},
        )
        if not updated_user:
            raise NotFoundData()

        await self.session_db.commit()
        await self.session_db.refresh(updated_user)
        return UserDTO.model_validate(updated_user)
