from typing import List, Optional, Union, Tuple

from sqlalchemy import delete, select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.courses.models import Course
from src.modules.courses.models_dto import CreateCourseDTO
from src.modules.student_courses.models import StudentCourse


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
        """Добавляет новый курс в базу"""
        return self.add(data)

    async def get_course_by_id(self, course_id: int) -> Course | None:
        """Находит курс по ID"""
        return await self.get_by_id(Course, course_id)

    async def get_course_by_slug(self, slug: str) -> Course | None:
        """Находит курс по уникальному slug"""
        result_db = await self.session.execute(
            select(Course).where(Course.slug == slug)
        )
        return result_db.scalar_one_or_none()

    async def get_all_courses(
        self,
        limit: int = 100,
        offset: int = 0,
        teacher_id: Optional[int] = None,
        include_deleted: Optional[bool] = False,
    ) -> Tuple[List[Course], int]:
        """Находит все курсы с учетом пагинации и фильтров и возвращает кортеж (курсы, общее_кол-во)"""
        stmt = select(Course)
        if teacher_id is not None:
            stmt = stmt.where(Course.teacher_id == teacher_id)
        if not include_deleted:
            stmt = stmt.where(Course.is_deleted == False)

        # Вычисляем общее количество
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await self.session.execute(count_stmt)).scalar() or 0

        # Получаем данные с учетом лимита
        stmt = stmt.limit(limit).offset(offset)
        result_db = await self.session.execute(stmt)
        courses = list(result_db.scalars().all())
        return courses, total_count

    async def get_courses_by_student_id(
        self,
        student_id: int,
        only_active: Optional[bool] = None,
        include_deleted: Optional[bool] = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Course], int]:
        """Находит все курсы, к которым есть доступ у студента"""
        stmt = (
            select(Course)
            .join(StudentCourse, StudentCourse.course_id == Course.id)
            .where(StudentCourse.student_id == student_id)
        )
        if only_active is True:
            stmt = stmt.where(
                (StudentCourse.expires_at.is_(None)) | (StudentCourse.expires_at > func.now())
            )
        elif only_active is False:
            stmt = stmt.where(
                (StudentCourse.expires_at.is_not(None)) & (StudentCourse.expires_at <= func.now())
            )
            
        if not include_deleted:
            stmt = stmt.where(Course.is_deleted == False)
            
        stmt = stmt.distinct()

        # Вычисляем общее количество
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_count = (await self.session.execute(count_stmt)).scalar() or 0

        stmt = stmt.limit(limit).offset(offset)
        result_db = await self.session.execute(stmt)
        courses = list(result_db.scalars().all())
        return courses, total_count

    async def update_course(
        self,
        course_id: int,
        values: dict,
    ) -> Course | None:
        """Обновляет данные курса по ID"""
        result_db = await self.session.execute(
            update(Course)
            .where(Course.id == course_id)
            .values(**values)
            .returning(Course)
        )
        return result_db.scalar_one_or_none()

    async def delete_course(self, course_id: int) -> Course | None:
        """Удаляет курс по ID"""
        result_db = await self.session.execute(
            delete(Course)
            .where(Course.id == course_id)
            .returning(Course)
        )
        return result_db.scalar_one_or_none()
