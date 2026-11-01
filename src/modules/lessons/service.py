from sqlalchemy import true
from src.modules.base.list_query import ListView, view_scope
from src.modules.homework_placements.service import HomeworkPlacementsService
from src.modules.check_permission.service import ObjectPermissionService
from src.modules.check_permission.repository import lesson_scope
from typing import Optional, Any
from uuid import UUID
from src.modules.teachers.models import Teacher
from src.modules.students.models import Student
from src.modules.lessons.models import RegularLessonSeries, RegularLessonOperation
from src.modules.lessons.models_dto import (
    PreviewRegularLessonsRequestDTO, ConfirmRegularLessonsRequestDTO,
    RegularLessonSpecDTO, RegularOperationResponseDTO, RegularSeriesResponseDTO,
)
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
        view: ListView = ListView.ALL,
        student_user_id: int | None = None,
    ) -> PaginationResponseDTO[LessonResponseDTO]:
        
        from src.modules.check_permission.repository import lesson_active_scope, lesson_student_filter
        if current_user.role == UserRole.STUDENT and student_user_id not in (None, current_user.id):
            raise PermissionErrorService()
        lessons, total = await self.lessons_repo.get_lessons(
            limit=limit, offset=offset, from_date=from_date, to_date=to_date,
            course_id=course_id, sort_date=sort_date, lesson_status=lesson_status,
            access_scope=lesson_scope(current_user.id, current_user.role)
                & view_scope(lesson_active_scope(current_user.id, current_user.role), view)
                & (lesson_student_filter(student_user_id) if student_user_id is not None else true()),
        )
        student = await self.student_repo.get_student_by_user_id(current_user.id) if current_user.role == UserRole.STUDENT else None
        student_id = student.id if student else None
        from src.modules.check_permission.read_context import ReadContextService
        items = [await self._visible_response(lesson, student_id, current_user, enrich=False) for lesson in lessons]
        flags = await self.lessons_repo.material_flags_many([d.id for d in items], current_user)
        for dto in items:
            dto.has_lecture, dto.has_homework = flags.get(dto.id, (False, False))
        items = await ReadContextService(self.session_db).lessons(items, current_user)
        if current_user.role == UserRole.TEACHER:
            rows = await self.lessons_repo.recipient_reminder_states(current_user.id, [d.id for d in items])
            for dto in items:
                from src.modules.lessons.models_dto import RecipientMaterialStatusDTO
                dto.recipient_materials = [RecipientMaterialStatusDTO(**{key: r[key] for key in RecipientMaterialStatusDTO.model_fields}) for r in rows if r['lesson_id'] == dto.id]
        return PaginationResponseDTO(items=items,
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
            await self.lessons_repo.lock_schedule(teacher_user_id)
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
            from src.modules.teacher_students.repository import TeacherStudentRepository
            lesson.lesson_price_kopecks = await TeacherStudentRepository(self.session_db).lesson_price(
                teacher.id, students[0].id)
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
            await self.lessons_repo.lock_schedule(teacher_user_id)
            await ObjectPermissionService(self.session_db).require(
                teacher_user_id, "lesson", lesson_id, write=True)
            teacher = await self.teacher_repo.get_teacher_by_user_id(teacher_user_id)
            lesson = await self.lessons_repo.get_lesson_by_id(lesson_id)
            if teacher is None or lesson.teacher_id != teacher.id:
                raise PermissionErrorService()
            from src.modules.base.versioning import check_updated_at
            check_updated_at(data.expected_updated_at, lesson.updated_at)
            values = data.model_dump(exclude_unset=True, exclude={"expected_updated_at"})
            moved = "scheduled_at" in values and values["scheduled_at"] != lesson.scheduled_at
            cancelled = values.get("status") == LessonStatus.CANCELLED and lesson.status != LessonStatus.CANCELLED
            restored = values.get("status") in (LessonStatus.SCHEDULED, LessonStatus.COMPLETED) and lesson.status == LessonStatus.CANCELLED
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
            elif restored:
                await notifications.lesson_event(lesson_id, "lesson_restored")
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
        from src.modules.check_permission.read_context import ReadContextService
        return (await ReadContextService(self.session_db).lessons([dto], actor))[0]

    async def delete_lesson(self, teacher_user_id: int, lesson_id: int) -> LessonResponseDTO:
        await self.lessons_repo.lock_schedule(teacher_user_id)
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
            return await self.get_lesson(await ObjectPermissionService(self.session_db).actor(teacher_user_id), lesson_id)
        await ObjectPermissionService(self.session_db).require(teacher_user_id, "course", lesson.course_id, write=True)
        from datetime import UTC
        deleted_lesson = await self.lessons_repo.update_lesson(
            lesson_id, {"is_deleted": True, "deleted_at": datetime.now(UTC)})
        await HomeworkPlacementsService(self.session_db).recalculate_course(lesson.course_id, "lesson_archived")
        await self.session_db.commit()

        return await self.get_lesson(await ObjectPermissionService(self.session_db).actor(teacher_user_id), lesson_id)

    async def _visible_response(self, lesson: Lesson, student_id: int | None, actor: UserDTO, enrich: bool = True) -> LessonResponseDTO:
        dto = self._response(lesson, student_id)
        if actor.role == UserRole.TEACHER:
            dto.course_name = lesson.course.name
            from src.modules.lessons.models_dto import LessonStudentLabelDTO
            dto.student_labels = [LessonStudentLabelDTO(user_id=ls.student.user_id,
                display_name=f'{ls.student.first_name} {ls.student.last_name}') for ls in lesson.lesson_students]
        if enrich:
            dto.has_lecture, dto.has_homework = await self.lessons_repo.material_flags(lesson.id, actor)
        if enrich:
            from src.modules.check_permission.read_context import ReadContextService
            return (await ReadContextService(self.session_db).lessons([dto], actor))[0]
        return dto


class RegularLessonsService(LessonsService):
    """Finite weekly batches. Preview and receipt are durable, writes are atomic."""

    async def _regular_teacher(self, user_id: int) -> Teacher:
        actor = await ObjectPermissionService(self.session_db).actor(user_id)
        if actor.role != UserRole.TEACHER:
            raise PermissionErrorService()
        teacher = await self.teacher_repo.get_teacher_by_user_id(user_id)
        if teacher is None:
            raise PermissionErrorService()
        return teacher

    async def _regular_operation(self, user_id: int, operation_id: UUID) -> RegularLessonOperation:
        from src.modules.base.exception import NotFoundData
        teacher = await self._regular_teacher(user_id)
        operation = await self.lessons_repo.regular_operation(operation_id)
        if operation is None or operation.teacher_id != teacher.id:
            raise NotFoundData()
        await ObjectPermissionService(self.session_db).require(user_id, "course", operation.course_id)
        return operation

    @staticmethod
    def _operation_response(operation: RegularLessonOperation) -> RegularOperationResponseDTO:
        from src.modules.lessons.models_dto import RegularOperationResponseDTO
        return RegularOperationResponseDTO(
            operation_id=operation.id, action=operation.request["action"],
            state="committed" if operation.result is not None else "preview",
            preview_revision=operation.preview_revision, preview=operation.preview,
            result=operation.result)

    async def get_operation(self, user_id: int, operation_id: UUID) -> RegularOperationResponseDTO:
        # Read receipt remains possible when the course becomes read-only.
        return self._operation_response(await self._regular_operation(user_id, operation_id))

    async def get_series(self, user_id: int, series_id: UUID) -> RegularSeriesResponseDTO:
        from src.modules.base.exception import NotFoundData
        from src.modules.lessons.models_dto import RegularSeriesResponseDTO
        teacher = await self._regular_teacher(user_id)
        series = await self.lessons_repo.regular_series(series_id, teacher.id)
        if series is None:
            raise NotFoundData()
        await ObjectPermissionService(self.session_db).require(user_id, "course", series.course_id)
        return RegularSeriesResponseDTO.model_validate(series)

    async def _regular_context(self, user_id: int, request: PreviewRegularLessonsRequestDTO) -> tuple[Teacher, Student, RegularLessonSpecDTO, RegularLessonSeries | None]:
        from src.modules.base.exception import NotFoundData, StaleUpdate
        from src.modules.lessons.models_dto import RegularLessonSpecDTO
        teacher = await self._regular_teacher(user_id)
        series = None
        if request.action == "create":
            spec = request.lesson
        else:
            series = await self.lessons_repo.regular_series(request.series_id, teacher.id)
            if series is None:
                raise NotFoundData()
            if request.action == "extend" and series.stopped:
                raise StaleUpdate("Серия остановлена. Создайте новую регулярную запись.")
            spec = RegularLessonSpecDTO.model_validate(series.spec)
        await ObjectPermissionService(self.session_db).require(user_id, "course", spec.course_id, write=True)
        course = await self.course_repo.get_course_by_id(spec.course_id)
        if course.teacher_id != teacher.id:
            raise PermissionErrorService()
        students = await self.lessons_repo.active_students(spec.course_id, teacher.id, spec.student_user_id)
        if len(students) != 1:
            raise InvalidLessonRequest("Нужен активный ученик, зачисленный на этот курс и связанный с преподавателем.")
        if series is None and await self.lessons_repo.regular_anchor_exists(
                teacher.id, spec.course_id, spec.student_user_id, spec.scheduled_at):
            raise StaleUpdate("Регулярная запись с этой первой датой уже существует. Откройте расписание.")
        return teacher, students[0], spec, series

    @staticmethod
    def _regular_dates(first: datetime, weeks: int) -> list[datetime]:
        from datetime import UTC
        from zoneinfo import ZoneInfo
        try:
            local = first.astimezone(ZoneInfo("Europe/Moscow"))
            return [(local + timedelta(weeks=n)).astimezone(UTC) for n in range(weeks)]
        except (OverflowError, ValueError) as exc:
            raise InvalidLessonRequest("Даты серии выходят за допустимый диапазон.") from exc

    async def _regular_preview(self, request: PreviewRegularLessonsRequestDTO, spec: RegularLessonSpecDTO, series: RegularLessonSeries | None, teacher_id: int) -> dict[str, Any]:
        from datetime import UTC
        now = datetime.now(UTC)
        occurrences = []
        # Private snapshot fields are used for compare, never sent as public DTO fields.
        versions = []
        if request.action in ("create", "extend"):
            try:
                first = spec.scheduled_at if series is None else series.through_at + timedelta(weeks=1)
            except OverflowError as exc:
                raise InvalidLessonRequest("Даты серии выходят за допустимый диапазон.") from exc
            dates = self._regular_dates(first, request.weeks)
            if dates[0] <= now:
                raise InvalidLessonRequest("Серия создаёт только будущие встречи. Выберите будущую первую дату.")
            for date in dates:
                end = self._end_time(date, spec.duration_minutes)
                conflicts = await self.lessons_repo.overlapping_ids(teacher_id, date, end, 0)
                occurrences.append(dict(scheduled_at=date.isoformat(), duration_minutes=spec.duration_minutes,
                                        lesson_id=None, conflict_lesson_ids=conflicts))
            for occurrence, date in zip(occurrences, dates):
                occurrence["conflict_occurrence_dates"] = [other.isoformat() for other in dates
                    if other != date and other < self._end_time(date, spec.duration_minutes)
                    and self._end_time(other, spec.duration_minutes) > date]
        elif request.action == "cancel_future":
            lessons = await self.lessons_repo.regular_lessons(series.id, now)
            for lesson in lessons:
                occurrences.append(dict(scheduled_at=lesson.scheduled_at.isoformat(),
                    duration_minutes=lesson.duration_minutes, lesson_id=lesson.id, conflict_lesson_ids=[]))
                versions.append([lesson.id, lesson.updated_at.isoformat()])
        return dict(course_id=spec.course_id, student_user_id=spec.student_user_id, title=spec.title,
                    timezone="Europe/Moscow", occurrences=occurrences, count=len(occurrences),
                    last_date=occurrences[-1]["scheduled_at"] if occurrences else None,
                    series_revision=series.revision if series else None, _versions=versions)

    async def preview_regular(self, user_id: int, request: PreviewRegularLessonsRequestDTO) -> RegularOperationResponseDTO:
        from src.modules.base.exception import StaleUpdate, NotFoundData
        try:
            await self.lessons_repo.lock_schedule(user_id)
            teacher = await self._regular_teacher(user_id)
            await self.lessons_repo.lock_regular_key(request.operation_id)
            existing = await self.lessons_repo.regular_operation(request.operation_id)
            payload = request.model_dump(mode="json", exclude={"weeks"} if request.action in ("stop", "cancel_future") else set())
            if existing is not None:
                if existing.teacher_id != teacher.id:
                    raise NotFoundData()
                if existing.request != payload:
                    raise StaleUpdate("Этот ключ операции уже использован с другими параметрами.")
                result = await self.get_operation(user_id, request.operation_id)
                await self.session_db.commit()
                return result
            teacher, student, spec, series = await self._regular_context(user_id, request)
            preview = await self._regular_preview(request, spec, series, teacher.id)
            operation = self.lessons_repo.add_regular_operation(
                id=request.operation_id, teacher_id=teacher.id, course_id=spec.course_id,
                series_id=series.id if series else None, request=payload, preview=preview,
                preview_revision=1)
            await self.session_db.flush()
            result = self._operation_response(operation)
            await self.session_db.commit()
            return result
        except Exception:
            await self.session_db.rollback()
            raise

    async def confirm_regular(self, user_id: int, operation_id: UUID, confirmation: ConfirmRegularLessonsRequestDTO) -> RegularOperationResponseDTO:
        from uuid import uuid4
        from src.modules.lessons.models_dto import PreviewRegularLessonsRequestDTO, CreateLessonDTO
        from src.modules.lessons.exception import RegularPreviewChanged
        from src.modules.base.exception import StaleUpdate
        try:
            await self.lessons_repo.lock_schedule(user_id)
            operation = await self._regular_operation(user_id, operation_id)
            # Return original receipt even after stop/transfer/archive; never repeat the write.
            if operation.result is not None:
                result = self._operation_response(operation)
                await self.session_db.commit()
                return result
            request = PreviewRegularLessonsRequestDTO.model_validate(operation.request)
            teacher, student, spec, series = await self._regular_context(user_id, request)
            preview = await self._regular_preview(request, spec, series, teacher.id)
            if preview != operation.preview:
                operation.preview = preview
                operation.preview_revision += 1
                await self.session_db.flush()
                refreshed = self._operation_response(operation).model_dump(mode="json")
                await self.session_db.commit()
                raise RegularPreviewChanged(refreshed)
            if confirmation.preview_revision != operation.preview_revision:
                raise RegularPreviewChanged(self._operation_response(operation).model_dump(mode="json"))
            if any(o["conflict_lesson_ids"] or o.get("conflict_occurrence_dates") for o in preview["occurrences"]) and not confirmation.acknowledge_conflicts:
                raise StaleUpdate("Подтвердите предупреждения о пересечениях перед созданием занятий.")
            if series is None:
                series = self.lessons_repo.add_regular_series(id=uuid4(), teacher_id=teacher.id,
                    course_id=spec.course_id, student_user_id=spec.student_user_id,
                    spec=spec.model_dump(mode="json"), anchor_at=spec.scheduled_at,
                    through_at=datetime.fromisoformat(preview["last_date"]), revision=1, stopped=False)
                await self.session_db.flush()
                operation.series_id = series.id
            else:
                series.revision += 1
            lesson_ids = []
            if request.action in ("create", "extend"):
                from src.modules.teacher_students.repository import TeacherStudentRepository
                price = await TeacherStudentRepository(self.session_db).lesson_price(teacher.id, student.id)
                for occurrence in preview["occurrences"]:
                    date = datetime.fromisoformat(occurrence["scheduled_at"])
                    values = spec.model_dump(exclude={"student_user_id", "scheduled_at"})
                    lesson = await self.lessons_repo.add_lesson(CreateLessonDTO(
                        teacher_id=teacher.id, scheduled_at=date, **values))
                    lesson.lesson_price_kopecks = price
                    self.lessons_repo.bind_regular_occurrence(lesson, series.id, date)
                    await self.session_db.flush()
                    await LessonStudentsRepository(self.session_db).add_student_to_lesson(
                        CreateLessonStudentDTO(lesson_id=lesson.id, student_id=student.id))
                    lesson_ids.append(lesson.id)
                series.through_at = datetime.fromisoformat(preview["last_date"])
            elif request.action == "stop":
                series.stopped = True
            elif request.action == "cancel_future":
                from src.modules.notifications.service import NotificationsService
                for occurrence in preview["occurrences"]:
                    lid = occurrence["lesson_id"]
                    await ObjectPermissionService(self.session_db).require(user_id, "lesson", lid, write=True)
                    await self.lessons_repo.update_lesson(lid, {"status": LessonStatus.CANCELLED})
                    await self.session_db.flush()
                    await NotificationsService(self.session_db).lesson_event(lid, "lesson_cancelled")
                    lesson_ids.append(lid)
            await self.session_db.flush()
            if request.action != "stop":
                await HomeworkPlacementsService(self.session_db).recalculate_course(spec.course_id, "regular_" + request.action)
            operation.result = dict(series_id=str(series.id), lesson_ids=lesson_ids,
                                    series_revision=series.revision, stopped=series.stopped)
            await self.session_db.flush()
            result = self._operation_response(operation)
            await self.session_db.commit()
            return result
        except Exception:
            await self.session_db.rollback()
            raise
