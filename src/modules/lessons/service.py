from src.modules.homework_placements.service import HomeworkPlacementsService
from src.modules.check_permission.service import ObjectPermissionService
from src.modules.check_permission.repository import lesson_scope
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.lessons.repository import LessonsRepository
from src.modules.lessons.models_dto import (
    LessonResponseDTO, 
    CreateLessonRequestDTO, 
    CreateLessonDTO, 
    UpdateLessonRequestDTO, ScheduleWarning
)
from src.modules.lessons.exception import LessonNotFound, InvalidLessonRequest
from src.modules.lessons.models import Lesson, LessonStatus
from src.modules.lesson_students.repository import LessonStudentsRepository
from src.modules.lesson_students.models_dto import CreateLessonStudentDTO
from src.modules.courses.repository import CourseRepository
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository
from src.modules.users.models_dto import UserDTO
from src.modules.users.models import UserRole
from src.modules.check_permission.exception import PermissionErrorService


class LessonsService:
    def __init__(
        self,
        lessons_repo: LessonsRepository,
        course_repo: CourseRepository,
        student_repo: StudentRepository,
        teacher_repo: TeacherRepository,
        session_db: AsyncSession,
    ) -> None:
        self.lessons_repo = lessons_repo
        self.course_repo = course_repo
        self.student_repo = student_repo
        self.teacher_repo = teacher_repo
        self.session_db = session_db

    async def get_lessons(
        self,
        current_user: UserDTO,
        limit: int,
        offset: int,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        course_id: Optional[int] = None,
        sort_date: str = "desc",
        lesson_status: LessonStatus | None = None,
    ) -> PaginationResponseDTO[LessonResponseDTO]:
        
        lessons, total = await self.lessons_repo.get_lessons(
            limit=limit, offset=offset, from_date=from_date, to_date=to_date,
            course_id=course_id, sort_date=sort_date, lesson_status=lesson_status,
            access_scope=lesson_scope(current_user.id, current_user.role),
        )
        student = await self.student_repo.get_student_by_user_id(current_user.id) if current_user.role == UserRole.STUDENT else None
        student_id = student.id if student else None
        return PaginationResponseDTO(items=[await self._visible_response(lesson, student_id, current_user) for lesson in lessons],
                                     total=total, limit=limit, offset=offset)

    @staticmethod
    def _response(lesson: Lesson, student_id: int | None) -> LessonResponseDTO:
        dto = LessonResponseDTO.model_validate(lesson)
        recipients = [ls for ls in lesson.lesson_students if student_id is None or ls.student_id == student_id]
        dto.has_lecture = any(ls.lectures for ls in recipients)
        dto.has_homework = any(ls.homeworks for ls in recipients)
        return dto

    async def get_lesson(self, current_user: UserDTO, lesson_id: int) -> LessonResponseDTO:
        await ObjectPermissionService(self.session_db).require(current_user.id, "lesson", lesson_id)
        lesson = await self.lessons_repo.get_lesson_by_id(lesson_id)
        student = await self.student_repo.get_student_by_user_id(current_user.id) if current_user.role == UserRole.STUDENT else None
        return await self._visible_response(lesson, student.id if student else None, current_user)

    async def create_lesson(self, teacher_user_id: int, data: CreateLessonRequestDTO) -> LessonResponseDTO:
        try:
            await ObjectPermissionService(self.session_db).require(
                teacher_user_id, "course", data.course_id, write=True)
            teacher = await self.teacher_repo.get_teacher_by_user_id(teacher_user_id)
            course = await self.course_repo.get_course_by_id(data.course_id)
            if teacher is None or course.teacher_id != teacher.id:
                raise PermissionErrorService()
            students = await self.lessons_repo.active_students(data.course_id, teacher.id, data.student_user_id)
            if not students:
                raise InvalidLessonRequest("The course needs an active enrolled student linked to this teacher")
            if len(students) != 1:
                raise InvalidLessonRequest("Specify student_user_id for a course with multiple students")
            self._end_time(data.scheduled_at, data.duration_minutes)
            lesson = await self.lessons_repo.add_lesson(CreateLessonDTO(
                teacher_id=teacher.id, **data.model_dump(exclude={"student_user_id"})))
            await self.session_db.flush()
            await LessonStudentsRepository(self.session_db).add_student_to_lesson(
                CreateLessonStudentDTO(lesson_id=lesson.id, student_id=students[0].id))
            await self.session_db.flush()
            await HomeworkPlacementsService(self.session_db).recalculate_course(lesson.course_id, "lesson_created")
            result = await self._write_response(lesson.id)
            await self.session_db.commit()
            return result
        except Exception:
            await self.session_db.rollback()
            raise

    async def update_lesson(self, teacher_user_id: int, lesson_id: int, data: UpdateLessonRequestDTO) -> LessonResponseDTO:
        try:
            await ObjectPermissionService(self.session_db).require(
                teacher_user_id, "lesson", lesson_id, write=True)
            teacher = await self.teacher_repo.get_teacher_by_user_id(teacher_user_id)
            lesson = await self.lessons_repo.get_lesson_by_id(lesson_id)
            if teacher is None or lesson.teacher_id != teacher.id:
                raise PermissionErrorService()
            values = data.model_dump(exclude_unset=True)
            moved = "scheduled_at" in values and values["scheduled_at"] != lesson.scheduled_at
            cancelled = values.get("status") == LessonStatus.CANCELLED and lesson.status != LessonStatus.CANCELLED
            self._end_time(values.get("scheduled_at", lesson.scheduled_at),
                           values.get("duration_minutes", lesson.duration_minutes))
            if values:
                await self.lessons_repo.update_lesson(lesson_id, values)
            await self.session_db.flush()
            await HomeworkPlacementsService(self.session_db).recalculate_course(lesson.course_id, "lesson_updated")
            from src.modules.notifications.service import NotificationsService
            notifications = NotificationsService(self.session_db)
            if cancelled:
                await notifications.lesson_event(lesson_id, "lesson_cancelled")
            elif moved:
                await notifications.lesson_event(lesson_id, "lesson_rescheduled")
            result = await self._write_response(lesson_id)
            await self.session_db.commit()
            return result
        except Exception:
            await self.session_db.rollback()
            raise

    @staticmethod
    def _end_time(start: datetime, duration: int) -> datetime:
        try:
            return start + timedelta(minutes=duration)
        except OverflowError as exc:
            raise InvalidLessonRequest("Lesson end is outside the supported datetime range") from exc

    async def _write_response(self, lesson_id: int) -> LessonResponseDTO:
        lesson = await self.lessons_repo.get_lesson_by_id(lesson_id)
        dto = self._response(lesson, None)
        actor = await ObjectPermissionService(self.session_db).actor(lesson.teacher.user_id)
        dto.has_lecture, dto.has_homework = await self.lessons_repo.material_flags(lesson.id, actor)
        if lesson.status != LessonStatus.CANCELLED and not lesson.is_deleted:
            conflicts = await self.lessons_repo.overlapping_ids(
                lesson.teacher_id, lesson.scheduled_at,
                self._end_time(lesson.scheduled_at, lesson.duration_minutes), lesson.id)
            if conflicts:
                dto.warnings = [ScheduleWarning(lesson_ids=conflicts)]
        return dto

    async def delete_lesson(self, teacher_user_id: int, lesson_id: int) -> LessonResponseDTO:
        await ObjectPermissionService(self.session_db).require(teacher_user_id, "lesson", lesson_id)
        teacher = await self.teacher_repo.get_teacher_by_user_id(teacher_user_id)
        if not teacher:
            raise PermissionErrorService("Teacher not found")

        lesson = await self.lessons_repo.get_lesson_by_id(lesson_id)
        if not lesson:
            raise LessonNotFound("Lesson not found")

        if lesson.teacher_id != teacher.id:
            raise PermissionErrorService("Access denied to delete this lesson")

        if lesson.is_deleted:
            return LessonResponseDTO.model_validate(lesson)
        await ObjectPermissionService(self.session_db).require(teacher_user_id, "course", lesson.course_id, write=True)
        from datetime import UTC
        deleted_lesson = await self.lessons_repo.update_lesson(
            lesson_id, {"is_deleted": True, "deleted_at": datetime.now(UTC)})
        await HomeworkPlacementsService(self.session_db).recalculate_course(lesson.course_id, "lesson_archived")
        await self.session_db.commit()

        return LessonResponseDTO.model_validate(deleted_lesson)

    async def _visible_response(self, lesson: Lesson, student_id: int | None, actor: UserDTO) -> LessonResponseDTO:
        dto = self._response(lesson, student_id)
        dto.has_lecture, dto.has_homework = await self.lessons_repo.material_flags(lesson.id, actor)
        return dto
