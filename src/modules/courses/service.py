from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.users.models_dto import UserDTO
from sqlalchemy import true
from src.modules.base.list_query import ListView, view_scope
from src.modules.handlers_files.avatar_transaction import atomic_avatar_upload, retire_avatar
from src.modules.check_permission.service import ObjectPermissionService
from pathlib import Path
from datetime import datetime, UTC
from typing import Optional, List, Tuple

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.courses.exception import CourseNotFound, CourseAlreadyExists, CourseAccessDenied
from src.modules.courses.models import AvatarCoursesType
from src.modules.courses.models_dto import (
    CreateCourseDTORequest,
    CreateCourseDTO,
    UpdateCourseDTO,
    UpdateCourseDTORequest,
    CoursesDTO,
    CoursesResponseDTO,
)
from src.modules.courses.repository import CourseRepository
from src.modules.handlers_files.compression_images import CompressionImages
from src.modules.handlers_files.converter_images import HandlerImages
from src.modules.path_builder import PathBuilder
from src.modules.student_courses.repository import StudentCoursesRepository
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
        student_courses_repo: StudentCoursesRepository,
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
        self.student_courses_repo = student_courses_repo
        self.path_builder = path_builder
        self.handler_images = handler_images
        self.compression_images = compression_images
        self.session_db = session_db

    async def _create_avatar(self, course_id: int, avatar: UploadFile) -> str:
        path = await self.handler_images.create_avatar()
        await self.handler_images.convert_to_webp(avatar, path)
        return str(path)

    async def create_course(
        self,
        teacher_id: int,
        data: CreateCourseDTORequest | CreateCourseDTO,
    ) -> CoursesDTO:
        """
        Создает курс
        """
        existing = await self.course_repo.get_course_by_slug(data.slug)
        if existing:
            raise CourseAlreadyExists(f"Course with slug '{data.slug}' already exists")

        course_data = data if isinstance(data, CreateCourseDTO) else CreateCourseDTO(
            teacher_id=teacher_id,
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
    ) -> Tuple[List[CoursesDTO], int]:
        """
        Возвращает кортеж (список курсов, общее количество).
        """
        courses, total = await self.course_repo.get_all_courses(
            limit=limit,
            offset=offset,
            include_deleted=True,
        )
        return [CoursesDTO.model_validate(course) for course in courses], total

    async def get_courses_by_teacher(
        self,
        teacher_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[CoursesDTO], int]:
        """
        Возвращает кортеж (список курсов, общее количество).
        """
        courses, total = await self.course_repo.get_all_courses(
            limit=limit,
            offset=offset,
            teacher_id=teacher_id,
            include_deleted=True,
        )
        return [CoursesDTO.model_validate(course) for course in courses], total

    async def get_courses_by_student(
        self,
        student_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[CoursesDTO], int]:
        """
        Возвращает кортеж (список курсов, общее количество) для студента или всех.
        """

        # для студента необходимо показывать удалённые курсы.
        if student_id is not None:
            courses, total = await self.course_repo.get_courses_by_student_id(
                student_id=student_id,
                only_active=True,
                include_deleted=True,
                limit=limit,
                offset=offset,
            )
            return [CoursesDTO.model_validate(course) for course in courses], total

    async def check_student_access(
        self,
        student_id: int,
        course_id: int,
    ) -> bool:
        """Проверяет доступ."""
        return await self.student_courses_repo.check_student_has_access_to_course(
            student_id=student_id,
            course_id=course_id,
        )

    async def get_course_by_id(
        self,
        course_id: int,
    ) -> CoursesDTO | None:
        """Находит курс по id"""
        course = await self.course_repo.get_course_by_id(course_id)
        return CoursesDTO.model_validate(course) if course else None

    async def get_course_by_slug(
        self,
        slug: str,
    ) -> CoursesDTO | None:
        """Находит курс по slug"""
        course = await self.course_repo.get_course_by_slug(slug)
        return CoursesDTO.model_validate(course) if course else None

    async def update_course(
        self,
        course_id: int,
        teacher_id: int,
        data: UpdateCourseDTO | UpdateCourseDTORequest,
    ) -> CoursesDTO:
        """Обновляет курс"""
        try:
            from src.modules.course_lifecycle.repository import LifecycleRepository
            course = await LifecycleRepository(self.session_db).course(course_id)
            if not course:
                raise CourseNotFound()
            if course.is_deleted:
                from src.modules.check_permission.exception import PermissionErrorService
                raise PermissionErrorService("Archived course is read-only")
            if course.teacher_id != teacher_id:
                raise CourseAccessDenied("You can only modify your own courses")

            from src.modules.base.versioning import check_updated_at
            check_updated_at(data.expected_updated_at, course.updated_at)

            if data.slug is not None and data.slug != course.slug:
                existing = await self.course_repo.get_course_by_slug(data.slug)
                if existing and existing.id != course_id:
                    raise CourseAlreadyExists(f"Course with slug '{data.slug}' already exists")

            values = data.model_dump(exclude_unset=True, exclude={"expected_updated_at"})
            # The legacy PATCH archive must preserve the same timestamp as DELETE.
            if values.get("is_deleted") is True:
                values["deleted_at"] = datetime.now(UTC)

            if data.avatar_type and data.avatar_type != AvatarCoursesType.CUSTOM:
                retire_avatar(self.session_db, course.avatar_path)
                values["avatar_path"] = None

            if not values:
                result = CoursesDTO.model_validate(course)
                await self.session_db.commit()
                return result

            updated_course = await self.course_repo.update_course(
                course_id=course_id,
                values=values,
            )
            if not updated_course:
                raise CourseNotFound()

            await self.session_db.commit()
            await self.session_db.refresh(updated_course)
            return CoursesDTO.model_validate(updated_course)

        except Exception:
            await self.session_db.rollback()
            raise

    @atomic_avatar_upload
    async def update_avatar(
        self,
        course_id: int,
        teacher_id: int,
        avatar: UploadFile,
    ) -> CoursesDTO:
        """Обновляет аватар"""
        from src.modules.course_lifecycle.repository import LifecycleRepository
        course = await LifecycleRepository(self.session_db).course(course_id)
        if not course:
            raise CourseNotFound()
            
        if course.is_deleted:
            from src.modules.check_permission.exception import PermissionErrorService
            raise PermissionErrorService("Archived course is read-only")
        if course.teacher_id != teacher_id:
            raise CourseAccessDenied("You can only modify your own courses")

        old_path = course.avatar_path
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

        retire_avatar(self.session_db, old_path)
        await self.session_db.commit()
        self.handler_images.upload_committed = True
        await self.session_db.refresh(updated_course)
        return CoursesDTO.model_validate(updated_course)

    async def soft_delete_course(
        self,
        course_id: int,
        teacher_id: int,
    ) -> CoursesDTO:
        """Мягкое удаление"""
        course = await self.course_repo.get_course_by_id(course_id)
        if not course:
            raise CourseNotFound()
        if course.is_deleted:
            return CoursesDTO.model_validate(course)
            
        if course.teacher_id != teacher_id:
            raise CourseAccessDenied("You can only modify your own courses")

        updated = await self.course_repo.update_course(
            course_id=course_id,
            values={
                "is_deleted": True,
                "deleted_at": datetime.now(UTC),
            },
        )
        if not updated:
            raise CourseNotFound()

        await self.session_db.commit()
        await self.session_db.refresh(updated)
        return CoursesDTO.model_validate(updated)

    async def delete_course(
        self,
        course_id: int,
        teacher_id: int,
    ) -> CoursesDTO:
        """Legacy hard delete is permanently closed; use the audited admin workflow."""
        from src.modules.check_permission.exception import PermissionErrorService
        raise PermissionErrorService("Purge is a separate admin workflow")

    async def list_visible(
        self, actor: UserDTO, limit: int, offset: int,
        teacher_user_id: int | None = None, view: ListView = ListView.ALL,
        student_user_id: int | None = None,
    ) -> PaginationResponseDTO[CoursesResponseDTO]:
        from src.modules.check_permission.repository import course_scope, course_active_scope, course_student_filter
        from src.modules.users.models import UserRole
        from src.modules.check_permission.exception import PermissionErrorService
        if actor.role == UserRole.STUDENT and student_user_id not in (None, actor.id):
            raise PermissionErrorService()
        teacher_id = None
        if teacher_user_id is not None:
            teacher = await self.teacher_repo.get_teacher_by_user_id(teacher_user_id)
            if teacher is None:
                return PaginationResponseDTO(items=[], total=0, limit=limit, offset=offset)
            teacher_id = teacher.id
        courses, total = await self.course_repo.get_all_courses(
            limit=limit, offset=offset, teacher_id=teacher_id, include_deleted=True,
            access_scope=course_scope(actor.id, actor.role) & view_scope(course_active_scope(actor.id, actor.role), view)
                & (course_student_filter(student_user_id) if student_user_id is not None else true()),
        )
        from src.modules.check_permission.read_context import ReadContextService
        items = await ReadContextService(self.session_db).courses([CoursesResponseDTO.model_validate(c) for c in courses], actor)
        return PaginationResponseDTO(items=items,
                                     total=total, limit=limit, offset=offset)

    async def detail_visible(self, actor, course_id: int):
        await ObjectPermissionService(self.session_db).require(actor.id, "course", course_id)
        from src.modules.check_permission.read_context import ReadContextService
        course = await self.course_repo.get_course_by_id(course_id)
        return (await ReadContextService(self.session_db).courses([CoursesResponseDTO.model_validate(course)], actor))[0]

    async def owner_profile(self, actor, course_id: int | None = None):
        from src.modules.check_permission.exception import PermissionErrorService
        from src.modules.users.models import UserRole
        if course_id is not None:
            await ObjectPermissionService(self.session_db).require(actor.id, "course", course_id, write=True)
        if actor.role != UserRole.TEACHER:
            raise PermissionErrorService()
        teacher = await self.teacher_repo.get_teacher_by_user_id(actor.id)
        if teacher is None:
            raise PermissionErrorService()
        return teacher

    async def avatar_file(self, actor, course_id: int) -> Path:
        from src.modules.base.exception import NotFoundData
        await ObjectPermissionService(self.session_db).require(actor.id, "course", course_id)
        course = await self.get_course_by_id(course_id)
        path = Path(course.avatar_path) if course.avatar_path else None
        if path is None:
            raise NotFoundData()
        return path

    async def personal_workspace(self, actor: UserDTO, student_user_id: int, create: bool = False) -> CoursesResponseDTO | None:
        """An explicit start is atomic/idempotent across concurrent tabs and retries."""
        from src.modules.teacher_students.repository import TeacherStudentRepository
        from src.modules.check_permission.exception import PermissionErrorService
        from src.modules.student_courses.models_dto import CreateStudentCoursesDTO
        from src.modules.audit_events.service import AuditEventsService
        from uuid import uuid4
        try:
            teacher = await self.owner_profile(actor)
            await ObjectPermissionService(self.session_db).require_link(actor.id, student_user_id)
            student = await self.student_repo.get_student_by_user_id(student_user_id)
            if student is None:
                raise CourseNotFound()
            if create:
                link = await TeacherStudentRepository(self.session_db).previous_link(teacher.id, student.id)
                if link is None or link.ended_at is not None:
                    raise PermissionErrorService()
            course = await self.course_repo.personal_course(teacher.id, student.id)
            if course is None and create:
                course = await self.course_repo.add_course(CreateCourseDTO(
                    teacher_id=teacher.id, name=f"{student.first_name} {student.last_name}",
                    slug="student-" + uuid4().hex))
                await self.session_db.flush()
                await self.student_courses_repo.add_student_to_course(CreateStudentCoursesDTO(
                    student_id=student.id, course_id=course.id))
                AuditEventsService(self.session_db).stage(actor.id, "personal_workspace_create", "course", course.id)
            course_id = course.id if course else None
            if create:
                await self.session_db.commit()
            return await self.detail_visible(actor, course_id) if course_id else None
        except Exception:
            await self.session_db.rollback()
            raise
