from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import BaseRepository
from src.modules.student_courses.models import StudentCourse


class StudentCoursesRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=StudentCourse,
        )

    async def check_student_has_access_to_course(
        self,
        student_id: int,
        course_id: int,
    ) -> bool:
        """Проверка привязки активного студента к активному курсу"""
        stmt = select(StudentCourse).where(
            StudentCourse.student_id == student_id,
            StudentCourse.course_id == course_id,
            StudentCourse.is_active == True,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None



