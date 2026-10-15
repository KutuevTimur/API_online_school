from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.base.exception import NotFoundData
from src.modules.teacher_students.repository import TeacherStudentRepository
from src.modules.teacher_students.models_dto import LinkTeacherStudentRequestDTO, TeacherStudentResponseDTO
from src.modules.teachers.repository import TeacherRepository
from src.modules.students.repository import StudentRepository
from src.modules.users.repository import UsersRepository
from src.modules.users.models import UserRole


class TeacherStudentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def link(self, data: LinkTeacherStudentRequestDTO) -> TeacherStudentResponseDTO:
        try:
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
            previous = await repo.previous_link(teacher.id, student.id)
            if previous is not None and previous.ended_at is not None:
                from datetime import datetime, UTC
                from src.modules.course_lifecycle.models import EnrollmentGap
                now = datetime.now(UTC)
                for membership in await repo.memberships(teacher.id, student.id):
                    if previous.ended_at < now:
                        self.session.add(EnrollmentGap(enrollment_id=membership.id,
                            started_at=previous.ended_at, ended_at=now))
            await repo.link(teacher.id, student.id)
            await self.session.commit()
            return TeacherStudentResponseDTO(**data.model_dump(), active=True)
        except Exception:
            await self.session.rollback()
            raise
