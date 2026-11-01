from sqlalchemy import select
from sqlalchemy.engine import Row
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

    async def lock_courses(self, teacher_id: int, student_id: int) -> list[int]:
        return list((await self.session.scalars(select(Course.id).join(StudentCourse).where(
            Course.teacher_id == teacher_id, StudentCourse.student_id == student_id)
            .order_by(Course.id).with_for_update(of=Course))).all())

    async def page(self, teacher_user_id: int | None, student_user_id: int | None,
                   active: bool | None, limit: int, offset: int) -> tuple[list[Row], int]:
        from sqlalchemy import func
        from src.modules.teachers.models import Teacher
        from src.modules.students.models import Student
        stmt = select(TeacherStudent, Teacher, Student).join(
            Teacher, Teacher.id == TeacherStudent.teacher_id).join(
            Student, Student.id == TeacherStudent.student_id)
        if teacher_user_id is not None:
            stmt = stmt.where(Teacher.user_id == teacher_user_id)
        if student_user_id is not None:
            stmt = stmt.where(Student.user_id == student_user_id)
        if active is not None:
            stmt = stmt.where(TeacherStudent.ended_at.is_(None) if active else TeacherStudent.ended_at.is_not(None))
        # The count anchor also returns the total for an out-of-range page.
        filtered = stmt.with_only_columns(TeacherStudent.id).cte("filtered_links")
        total = select(func.count().label("total")).select_from(filtered).subquery()
        page = select(TeacherStudent).where(TeacherStudent.id.in_(select(filtered.c.id))).order_by(
            TeacherStudent.id).limit(limit).offset(offset).subquery()
        from sqlalchemy.orm import aliased
        from sqlalchemy import true
        from src.modules.users.models import User
        link = aliased(TeacherStudent, page)
        teacher_user, student_user = aliased(User), aliased(User)
        rows = (await self.session.execute(select(link, Teacher, Student,
            teacher_user.username, student_user.username, total.c.total).select_from(
            total.outerjoin(page, true())).outerjoin(Teacher, Teacher.id == link.teacher_id)
            .outerjoin(Student, Student.id == link.student_id)
            .outerjoin(teacher_user, teacher_user.id == Teacher.user_id)
            .outerjoin(student_user, student_user.id == Student.user_id)
            .order_by(link.id))).all()
        return [row for row in rows if row[0] is not None], rows[0][-1]

    async def lesson_price(self, teacher_id: int, student_id: int) -> int | None:
        return await self.session.scalar(select(TeacherStudent.lesson_price_kopecks).where(
            TeacherStudent.teacher_id == teacher_id, TeacherStudent.student_id == student_id,
            TeacherStudent.ended_at.is_(None)))
