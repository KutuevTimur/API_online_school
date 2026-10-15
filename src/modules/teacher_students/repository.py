from sqlalchemy import select
from src.modules.courses.models import Course
from src.modules.student_courses.models import StudentCourse
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.base.repository_model import BaseRepository
from src.modules.teacher_students.models import TeacherStudent


class TeacherStudentRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=TeacherStudent)

    async def link(self, teacher_id: int, student_id: int) -> TeacherStudent:
        stmt = insert(TeacherStudent).values(teacher_id=teacher_id, student_id=student_id)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_teacher_students_pair", set_={"ended_at": None}
        ).returning(TeacherStudent)
        return (await self.session.execute(stmt.execution_options(populate_existing=True))).scalar_one()

    async def previous_link(self, teacher_id: int, student_id: int) -> TeacherStudent | None:
        return await self.session.scalar(select(TeacherStudent).where(
            TeacherStudent.teacher_id == teacher_id, TeacherStudent.student_id == student_id)
            .with_for_update().execution_options(populate_existing=True))

    async def memberships(self, teacher_id: int, student_id: int) -> list[StudentCourse]:
        return list((await self.session.scalars(select(StudentCourse).join(Course).where(
            Course.teacher_id == teacher_id, StudentCourse.student_id == student_id)
            .order_by(StudentCourse.id).with_for_update(of=StudentCourse))).all())
