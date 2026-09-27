from typing import Sequence
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.student_courses.models import StudentCourse
from src.modules.student_courses.models_dto import CreateStudentCoursesDTO


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
        """Проверка прав доступа (активная подписка на курс)"""
        stmt = select(StudentCourse).where(
            StudentCourse.student_id == student_id,
            StudentCourse.course_id == course_id,
            StudentCourse.is_deleted == False,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def get_student_course(
        self,
        student_id: int,
        course_id: int,
    ) -> StudentCourse | None:
        """Получить запись о зачислении (включая неактивные для восстановления)"""
        stmt = select(StudentCourse).where(
            StudentCourse.student_id == student_id,
            StudentCourse.course_id == course_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def add_student_to_course(
        self,
        data: CreateStudentCoursesDTO,
    ) -> StudentCourse:
        result_data = data.model_dump(exclude_unset=True)
        return self.add(result_data)

    async def get_students_for_course(
        self,
        course_id: int,
        limit: int,
        offset: int,
    ) -> tuple[int, Sequence[StudentCourse]]:
        """Получить список всех активных учеников, прикрепленных к курсу"""
        # Сначала считаем общее количество
        count_stmt = select(StudentCourse.id).where(
            StudentCourse.course_id == course_id,
            StudentCourse.is_deleted == False
        )
        count_res = await self.session.execute(count_stmt)
        total_count = len(count_res.scalars().all())

        # Потом получаем данные
        stmt = (
            select(StudentCourse)
            .where(
                StudentCourse.course_id == course_id,
                StudentCourse.is_deleted == False
            )
            .options(selectinload(StudentCourse.student))
            .limit(limit)
            .offset(offset)
            .order_by(StudentCourse.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return total_count, result.scalars().all()
