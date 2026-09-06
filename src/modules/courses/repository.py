from typing import List, Optional, Union

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.database_model import BaseRepository
from src.modules.courses.models import Course
from src.modules.courses.models_dto import CreateCourseDTO
from src.modules.student_courses.models import StudentCourse
from src.modules.teacher_couses.models import TeacherCourse


class CourseRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=Course,
        )

    async def add_course(
        self,
        data: Union[CreateCourseDTO, dict],
    ) -> Course:
        """Добавление нового курса в сессию"""
        return self.add(data)

    async def get_course_by_id(self, course_id: int) -> Course | None:
        """Получение курса по ID"""
        return await self.get_by_id(Course, course_id)

    async def get_course_by_slug(self, slug: str) -> Course | None:
        """Получение курса по уникальному slug"""
        result_db = await self.session.execute(
            select(Course).where(Course.slug == slug)
        )
        return result_db.scalar_one_or_none()

    async def get_all_courses(
        self,
        limit: int = 100,
        offset: int = 0,
        is_active: Optional[bool] = None,
        teacher_id: Optional[int] = None,
    ) -> List[Course]:
        """Получение списка всех курсов с пагинацией и опциональным фильтром активности и учителя"""
        stmt = select(Course)
        if is_active is not None:
            stmt = stmt.where(Course.is_active == is_active)
        if teacher_id is not None:
            stmt = (
                stmt.join(TeacherCourse, TeacherCourse.course_id == Course.id)
                .where(
                    (TeacherCourse.teacher_id == teacher_id) &
                    (TeacherCourse.is_active == True)
                )
            )

        stmt = stmt.limit(limit).offset(offset)

        result_db = await self.session.execute(stmt)
        return list(result_db.scalars().all())

    async def get_courses_by_student_id(
        self,
        student_id: int,
        only_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Course]:
        """Получение списка курсов, к которым привязан конкретный студент"""
        stmt = (
            select(Course)
            .join(StudentCourse, StudentCourse.course_id == Course.id)
            .where(StudentCourse.student_id == student_id)
        )
        if only_active is not None:
            stmt = stmt.where(
                StudentCourse.is_active == only_active,
                Course.is_active == only_active,
            )
        stmt = stmt.distinct().limit(limit).offset(offset)

        result_db = await self.session.execute(stmt)
        return list(result_db.scalars().all())

    async def update_course(
        self,
        course_id: int,
        values: dict,
    ) -> Course | None:
        """Обновление данных курса по ID"""
        result_db = await self.session.execute(
            update(Course)
            .where(Course.id == course_id)
            .values(**values)
            .returning(Course)
        )
        return result_db.scalar_one_or_none()

    async def delete_course(self, course_id: int) -> Course | None:
        """Удаление курса по ID"""
        result_db = await self.session.execute(
            delete(Course)
            .where(Course.id == course_id)
            .returning(Course)
        )
        return result_db.scalar_one_or_none()
