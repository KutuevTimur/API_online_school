from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.base.exception import NotFoundData
from src.modules.teacher_students.repository import TeacherStudentRepository
from src.modules.teacher_students.models_dto import (
    LinkTeacherStudentRequestDTO, TeacherStudentResponseDTO, AdminTeacherStudentResponseDTO,
)
from src.modules.users.models_dto import MinimalProfileResponseDTO
from src.modules.teachers.models import Teacher
from src.modules.students.models import Student
from src.modules.teachers.repository import TeacherRepository
from src.modules.students.repository import StudentRepository
from src.modules.users.repository import UsersRepository
from src.modules.users.models import UserRole


class TeacherStudentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def link(self, data: LinkTeacherStudentRequestDTO, actor_user_id: int) -> TeacherStudentResponseDTO:
        try:
            from src.modules.check_permission.service import ObjectPermissionService
            from src.modules.check_permission.exception import PermissionErrorService
            if (await ObjectPermissionService(self.session).actor(actor_user_id)).role != UserRole.ADMIN:
                raise PermissionErrorService()
            users = UsersRepository(self.session)
            teacher_user = await users.get_user_by_id(data.teacher_user_id)
            student_user = await users.get_user_by_id(data.student_user_id)
            if not teacher_user or teacher_user.role != UserRole.TEACHER or not student_user or student_user.role != UserRole.STUDENT:
                raise NotFoundData()
            teacher = await TeacherRepository(self.session).get_teacher_by_user_id(data.teacher_user_id)
            student = await StudentRepository(self.session).get_student_by_user_id(data.student_user_id)
            if teacher is None or student is None:
                raise NotFoundData()
            repo = TeacherStudentRepository(self.session)
            # Course locks precede enrollment/teacher-link locks, as in homework writes.
            course_ids = await repo.lock_courses(teacher.id, student.id)
            previous = await repo.previous_link(teacher.id, student.id)
            if previous is not None and previous.ended_at is not None:
                from datetime import datetime, UTC
                from src.modules.course_lifecycle.models import EnrollmentGap
                now = datetime.now(UTC)
                for membership in await repo.memberships(teacher.id, student.id):
                    if previous.ended_at < now:
                        self.session.add(EnrollmentGap(enrollment_id=membership.id,
                            started_at=previous.ended_at, ended_at=now))
            link = await repo.link(teacher.id, student.id)
            from src.modules.homework_placements.service import HomeworkPlacementsService
            for course_id in course_ids:
                await HomeworkPlacementsService(self.session).recalculate_course(course_id, "teacher_link_restored")
            from src.modules.audit_events.service import AuditEventsService
            AuditEventsService(self.session).stage(actor_user_id, "teacher_student_link", "teacher_student", link.id)
            await self.session.commit()
            return TeacherStudentResponseDTO(**data.model_dump(), active=True)
        except Exception:
            await self.session.rollback()
            raise

    async def page(self, actor_user_id: int, teacher_user_id: int | None,
                   student_user_id: int | None, active: bool | None, limit: int, offset: int
                   ) -> tuple[list[AdminTeacherStudentResponseDTO], int]:
        from src.modules.check_permission.service import ObjectPermissionService
        from src.modules.check_permission.exception import PermissionErrorService
        if (await ObjectPermissionService(self.session).actor(actor_user_id)).role != UserRole.ADMIN:
            raise PermissionErrorService()
        rows, total = await TeacherStudentRepository(self.session).page(
            teacher_user_id, student_user_id, active, limit, offset)
        def profile(value: Teacher | Student, username: str) -> MinimalProfileResponseDTO:
            return MinimalProfileResponseDTO(user_id=value.user_id, username=username,
                first_name=value.first_name, last_name=value.last_name,
                school_grade=value.school_grade if isinstance(value, Student) else None,
                avatar_path=f"/users/{value.user_id}/avatar" if value.avatar_path else None)

        items = []
        for link, teacher, student, teacher_name, student_name, _ in rows:
            items.append(AdminTeacherStudentResponseDTO(teacher_user_id=teacher.user_id,
                student_user_id=student.user_id, active=link.ended_at is None,
                ended_at=link.ended_at, teacher=profile(teacher, teacher_name),
                student=profile(student, student_name)))
        return items, total

    async def end(self, data: LinkTeacherStudentRequestDTO, actor_user_id: int) -> None:
        from datetime import UTC, datetime
        from src.modules.check_permission.service import ObjectPermissionService
        from src.modules.check_permission.exception import PermissionErrorService
        from src.modules.homework_placements.service import HomeworkPlacementsService
        from src.modules.audit_events.service import AuditEventsService
        try:
            if (await ObjectPermissionService(self.session).actor(actor_user_id)).role != UserRole.ADMIN:
                raise PermissionErrorService()
            teacher = await TeacherRepository(self.session).get_teacher_by_user_id(data.teacher_user_id)
            student = await StudentRepository(self.session).get_student_by_user_id(data.student_user_id)
            if teacher is None or student is None:
                raise NotFoundData()
            repo = TeacherStudentRepository(self.session)
            course_ids = await repo.lock_courses(teacher.id, student.id)
            link = await repo.previous_link(teacher.id, student.id)
            if link is None:
                raise NotFoundData()
            await repo.memberships(teacher.id, student.id)
            if link.ended_at is None:
                link.ended_at = datetime.now(UTC)
                await self.session.flush()
                for course_id in course_ids:
                    await HomeworkPlacementsService(self.session).recalculate_course(course_id, "teacher_link_ended")
                AuditEventsService(self.session).stage(actor_user_id, "teacher_student_end", "teacher_student", link.id)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
