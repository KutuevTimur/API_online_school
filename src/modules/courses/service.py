import shutil
import uuid
from pathlib import Path
from typing import Optional, List

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.courses.exception import CourseNotFound, CourseAvatarNotFound, CourseAlreadyExists
from src.modules.courses.models import AvatarCoursesType
from src.modules.courses.models_dto import (
    CreateCourseDTORequest,
    CreateCourseDTO,
    UpdateCourseDTO,
    UpdateCourseDTORequest,
    CoursesDTO,
)
from src.modules.courses.repository import CourseRepository
from src.modules.handlers_files.compression_images import CompressionImages
from src.modules.handlers_files.converter_images import HandlerImages
from src.modules.path_builder import PathBuilder
from src.modules.students.repository import StudentRepository
from src.modules.students.service import StudentService
from src.modules.teachers.repository import TeacherRepository
from src.modules.teachers.service import TeacherService


class CoursesService:

    def __init__(
        self,
        course_repo: CourseRepository,
        teacher_repo: TeacherRepository,
        teacher_service: TeacherService,
        student_repo: StudentRepository,
        student_service: StudentService,
        path_builder: PathBuilder,
        handler_images: HandlerImages,
        compression_images: CompressionImages,
        session_db: AsyncSession,
    ):
        self.course_repo = course_repo
        self.teacher_repo = teacher_repo
        self.teacher_service = teacher_service
        self.student_repo = student_repo
        self.student_service = student_service
        self.path_builder = path_builder
        self.handler_images = handler_images
        self.compression_images = compression_images
        self.session_db = session_db

    async def _create_avatar(self, course_id: int, avatar: UploadFile) -> str:
        """
        Преобразовывает в формат .webp и сжимает фото до 512x512.
        :return: Путь к аватарке
        :raises InvalidImageFormat: Если расширение или формат файла недопустимы / повреждены.
        :raises ImageConversionError: При ошибке в процессе конвертации.
        :raises ImageCompressionError: При ошибке сжатия / сохранения.
        """
        temp_webp: Path | None = None
        result_file_path: Path | None = None
        try:
            temp_webp = self.path_builder.get_temp() / Path(f"{uuid.uuid4().hex}.webp")
            temp_webp = await self.handler_images.convert_to_webp(photo=avatar, dest=temp_webp)

            result_file_path = self.path_builder.get_avatar_course(course_id)
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

    def delete_avatar(self, course_id: int) -> None:
        """
        Удаление аватарки курса на диске
        :raises CourseAvatarNotFound: Если аватар не найден
        """
        avatar_path = self.path_builder.get_avatar_course(course_id)
        if avatar_path.is_file():
            shutil.rmtree(avatar_path.parent)
        else:
            raise CourseAvatarNotFound()

    async def create_course(
        self,
        data: CreateCourseDTORequest | CreateCourseDTO,
    ) -> CoursesDTO:
        """
        Создание нового курса.
        :raises CourseAlreadyExists: Если курс с таким slug уже существует.
        """
        existing = await self.course_repo.get_course_by_slug(data.slug)
        if existing:
            raise CourseAlreadyExists(f"Course with slug '{data.slug}' already exists")

        course_data = data if isinstance(data, CreateCourseDTO) else CreateCourseDTO(
            **(data.model_dump(exclude_unset=True, exclude_none=True))
        )
        course = await self.course_repo.add_course(data=course_data)
        await self.session_db.commit()
        await self.session_db.refresh(course)
        return CoursesDTO.model_validate(course)

    async def get_all_courses(
        self,
        limit: int = 100,
        offset: int = 0,
        is_active: Optional[bool] = None,
    ) -> List[CoursesDTO]:
        """
        Получение всех курсов с пагинацией (limit, offset) и опциональным фильтром активности.
        """
        courses = await self.course_repo.get_all_courses(
            limit=limit,
            offset=offset,
            is_active=is_active,
        )
        return [CoursesDTO.model_validate(course) for course in courses]

    async def get_courses(
        self,
        student_id: Optional[int] = None,
        is_active: Optional[bool] = True,
        limit: int = 100,
        offset: int = 0,
    ) -> List[CoursesDTO]:
        """
        Получение курсов (с фильтрацией по студенту или всех) с пагинацией (limit, offset).
        """
        if student_id is not None:
            courses = await self.course_repo.get_courses_by_student_id(
                student_id=student_id,
                only_active=is_active,
                limit=limit,
                offset=offset,
            )
            return [CoursesDTO.model_validate(course) for course in courses]

        return await self.get_all_courses(
            limit=limit,
            offset=offset,
            is_active=is_active,
        )

    async def get_course_by_id(
        self,
        course_id: int,
    ) -> CoursesDTO | None:
        """
        Получение конкретного курса по ID.
        """
        course = await self.course_repo.get_course_by_id(course_id)
        return CoursesDTO.model_validate(course) if course else None

    async def get_course_by_slug(
        self,
        slug: str,
    ) -> CoursesDTO | None:
        """
        Получение конкретного курса по slug.
        """
        course = await self.course_repo.get_course_by_slug(slug)
        return CoursesDTO.model_validate(course) if course else None

    async def update_course(
        self,
        course_id: int,
        data: UpdateCourseDTO | UpdateCourseDTORequest,
    ) -> CoursesDTO:
        """
        Обновление данных курса по ID.
        :raises CourseNotFound: Если курс не найден.
        :raises CourseAlreadyExists: Если новый slug уже занят.
        """
        course = await self.course_repo.get_course_by_id(course_id)
        if not course:
            raise CourseNotFound()

        # Проверка уникальности slug при его обновлении
        if not data.slug is None and data.slug != course.slug:
            existing = await self.course_repo.get_course_by_slug(data.slug)
            if existing and existing.id != course_id:
                raise CourseAlreadyExists(f"Course with slug '{data.slug}' already exists")

        # Если avatar_type переключается со стандартного на дефолтный/иной, удаляем старый файл кастомной аватарки
        if data.avatar_type and data.avatar_type != AvatarCoursesType.CUSTOM:
            try:
                self.delete_avatar(course_id=course_id)
            except CourseAvatarNotFound:
                pass
            data.avatar_path = None

        values = data.model_dump(exclude_unset=True)

        if not values:
            return CoursesDTO.model_validate(course)

        updated_course = await self.course_repo.update_course(
            course_id=course_id,
            values=values,
        )
        if not updated_course:
            raise CourseNotFound()

        await self.session_db.commit()
        await self.session_db.refresh(updated_course)
        return CoursesDTO.model_validate(updated_course)

    async def update_avatar(
        self,
        course_id: int,
        avatar: UploadFile,
    ) -> CoursesDTO:
        """
        Обновление аватарки курса: конвертирует в .webp, сжимает и сохраняет на диск,
        затем обновляет avatar_path и avatar_type на CUSTOM в БД.
        :raises CourseNotFound: Если курс не найден.
        :raises InvalidImageFormat: Если формат файла не поддерживается.
        """
        course = await self.course_repo.get_course_by_id(course_id)
        if not course:
            raise CourseNotFound()

        try:
            self.delete_avatar(course_id=course_id)
        except CourseAvatarNotFound:
            pass

        avatar_path = await self._create_avatar(course_id=course_id, avatar=avatar)

        updated_course = await self.course_repo.update_course(
            course_id=course_id,
            values={
                "avatar_path": avatar_path,
                "avatar_type": AvatarCoursesType.CUSTOM,
            },
        )
        if not updated_course:
            raise CourseNotFound()

        await self.session_db.commit()
        await self.session_db.refresh(updated_course)
        return CoursesDTO.model_validate(updated_course)

    async def delete_course(
        self,
        course_id: int,
    ) -> CoursesDTO:
        """
        Удаление курса по ID с подчисткой аватарки на диске.
        :raises CourseNotFound: Если курс не найден.
        """
        course = await self.course_repo.get_course_by_id(course_id)
        if not course:
            raise CourseNotFound()

        try:
            self.delete_avatar(course_id=course_id)
        except CourseAvatarNotFound:
            pass

        deleted = await self.course_repo.delete_course(course_id=course_id)
        if not deleted:
            raise CourseNotFound()

        await self.session_db.commit()
        return CoursesDTO.model_validate(deleted)
