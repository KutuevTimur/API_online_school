from typing import List

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import BaseRepository
from src.modules.teacher_couses.models import TeacherCourse
from src.modules.teacher_couses.models_dto import CreateTeacherCoursesDTO


class TeacherCoursesRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=TeacherCourse,
        )

    async def add_teacher_courses(
        self,
        data: CreateTeacherCoursesDTO,
    ) -> TeacherCourse:
        """Добавление новой записи в сессию"""
        return self.add(data)

    async def get_teacher_courses_by_id(self, teacher_courses_id: int) -> TeacherCourse | None:
        """Получение преподавателя по ID"""
        return await self.get_by_id(TeacherCourse, teacher_courses_id)

    async def get_teacher_course(self, teacher_id: int, course_id: int) -> TeacherCourse | None:
        result_db = await self.session.execute(
            select(TeacherCourse)
            .where(
                (TeacherCourse.teacher_id == teacher_id) &
                (TeacherCourse.course_id == course_id)
            )
        )
        return result_db.scalar_one_or_none()

    async def get_teacher_courses_by_teacher_id(self, teacher_id: int) -> List[TeacherCourse]:
        result_db = await self.session.execute(select(TeacherCourse).where(TeacherCourse.teacher_id == teacher_id))
        return list(result_db.scalars().all())

    async def get_teacher_courses_by_course_id(self, course_id: int) -> List[TeacherCourse]:
        result_db = await self.session.execute(select(TeacherCourse).where(TeacherCourse.course_id == course_id))
        return list(result_db.scalars().all())

    async def set_is_active_teacher_courses(
        self,
        course_id: int,
        teacher_id: int,
        is_active: bool
    ) -> TeacherCourse | None:
        result_db = await self.session.execute(
            update(TeacherCourse)
            .where(
                (TeacherCourse.teacher_id == teacher_id) &
                (TeacherCourse.course_id == course_id)
            )
            .values(is_active=is_active)
            .returning(TeacherCourse)
        )
        return result_db.scalar_one_or_none()

    async def delete_teacher_courses(
        self,
        course_id: int,
        teacher_id: int,
    ) -> TeacherCourse | None:
        result_db = await self.session.execute(
            delete(TeacherCourse)
            .where(
                (TeacherCourse.teacher_id == teacher_id) &
                (TeacherCourse.course_id == course_id)
            )
            .returning(TeacherCourse)
        )
        return result_db.scalar_one_or_none()
