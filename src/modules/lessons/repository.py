from typing import Tuple, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import update, delete, select, func, literal, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.lessons.models import Lesson, LessonStatus
from src.modules.courses.models import Course
from src.modules.student_courses.models import StudentCourse
from src.modules.teacher_students.models import TeacherStudent
from src.modules.students.models import Student
from src.modules.users.models import User, UserRole
from src.modules.lesson_students.models import LessonStudent
from src.modules.lessons.models_dto import CreateLessonDTO


class LessonsRepository(BaseRepository):

    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=Lesson,
        )

    async def add_lesson(
        self,
        data: CreateLessonDTO,
    ) -> Lesson:
        """Добавляет новое занятие"""
        return self.add(data)

    async def get_lesson_by_id(self, lesson_id: int) -> Lesson | None:
        """Получает урок по ID (с жадной загрузкой связей для формирования флагов)"""
        stmt = (
            select(Lesson)
            .where(Lesson.id == lesson_id)
            .execution_options(populate_existing=True)
            .options(
                selectinload(Lesson.lesson_students).selectinload(LessonStudent.lectures),
                selectinload(Lesson.lesson_students).selectinload(LessonStudent.homeworks)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_lessons(
        self,
        limit: int = 100,
        offset: int = 0,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        course_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        student_id: Optional[int] = None,
        sort_date: str = "desc",
        lesson_status: LessonStatus | None = None,
        access_scope=None,
    ) -> Tuple[List[Lesson], int]:
        """Получает список уроков с фильтрацией, пагинацией и сортировкой.
        Scope применяется до подсчёта и пагинации."""
        stmt = select(Lesson)
        if access_scope is not None:
            stmt = stmt.where(access_scope)

        if lesson_status is not None:
            stmt = stmt.where(Lesson.status == lesson_status)

        # Base filters
        if from_date:
            stmt = stmt.where(Lesson.scheduled_at >= from_date)
        if to_date:
            stmt = stmt.where(Lesson.scheduled_at <= to_date)
        if course_id:
            stmt = stmt.where(Lesson.course_id == course_id)
        if teacher_id:
            stmt = stmt.where(Lesson.teacher_id == teacher_id)
            
        if student_id:
            stmt = stmt.join(Lesson.lesson_students).where(LessonStudent.student_id == student_id)

        total = await self.session.scalar(select(func.count()).select_from(stmt.subquery())) or 0

        # Pagination & Ordering
        if sort_date.lower() == "asc":
            stmt = stmt.order_by(Lesson.scheduled_at.asc())
        else:
            stmt = stmt.order_by(Lesson.scheduled_at.desc())
            
        stmt = stmt.limit(limit).offset(offset)
        
        stmt = stmt.options(
            selectinload(Lesson.lesson_students).selectinload(LessonStudent.lectures),
            selectinload(Lesson.lesson_students).selectinload(LessonStudent.homeworks)
        )

        result = await self.session.execute(stmt)
        rows = result.all()
        
        if not rows:
            return [], total
            
        lessons = [row[0] for row in rows]

        return lessons, total

    async def update_lesson(self, lesson_id: int, values: dict) -> Lesson:
        """Обновляет поля у урока"""
        stmt = (
            update(Lesson)
            .where(Lesson.id == lesson_id)
            .values(**values)
            .returning(Lesson)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete_lesson(self, lesson_id: int) -> Lesson:
        """Удаляет урок, возвращая удаленный объект"""
        stmt = (
            delete(Lesson)
            .where(Lesson.id == lesson_id)
            .returning(Lesson)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def material_flags(self, lesson_id, actor):
        from src.modules.lectures.models import Lecture
        from src.modules.homeworks.models import Homework
        from src.modules.check_permission.repository import material_scope
        flags = []
        for model in (Lecture, Homework):
            flags.append(bool(await self.session.scalar(select(func.count()).select_from(model).join(
                LessonStudent, LessonStudent.id == model.lesson_student_id).where(
                    LessonStudent.lesson_id == lesson_id, material_scope(model, actor.id, actor.role)))))
        from src.modules.homework_placements.models import HomeworkPlacement
        flags[1] = bool(await self.session.scalar(select(func.count()).select_from(HomeworkPlacement)
            .join(LessonStudent, LessonStudent.id == HomeworkPlacement.lesson_student_id)
            .join(Homework, Homework.id == HomeworkPlacement.homework_id).where(
                LessonStudent.lesson_id == lesson_id, material_scope(HomeworkPlacement, actor.id, actor.role),
                material_scope(Homework, actor.id, actor.role))))
        return tuple(flags)

    async def active_students(self, course_id: int, teacher_id: int,
                              student_user_id: int | None = None) -> list[Student]:
        stmt = (select(Student).join(User, User.id == Student.user_id)
                .join(StudentCourse, StudentCourse.student_id == Student.id)
                .join(TeacherStudent, TeacherStudent.student_id == Student.id)
                .where(StudentCourse.course_id == course_id,
                       StudentCourse.is_deleted.is_(False),
                       StudentCourse.access_ended_at.is_(None),
                       StudentCourse.history_revoked.is_(False),
                       or_(StudentCourse.expires_at.is_(None), StudentCourse.expires_at > func.clock_timestamp()),
                       StudentCourse.started_at <= func.clock_timestamp(),
                       TeacherStudent.teacher_id == teacher_id, TeacherStudent.ended_at.is_(None),
                       User.is_active.is_(True), User.role == UserRole.STUDENT)
                .order_by(Student.id).with_for_update(of=(StudentCourse, TeacherStudent, User)))
        if student_user_id is not None:
            stmt = stmt.where(Student.user_id == student_user_id)
        return list((await self.session.scalars(stmt)).all())

    async def overlapping_ids(self, teacher_id: int, start: datetime, end: datetime,
                              exclude_id: int) -> list[int]:
        stmt = (select(Lesson.id).join(Course, Course.id == Lesson.course_id)
                .where(Lesson.teacher_id == teacher_id, Lesson.id != exclude_id,
                       Lesson.is_deleted.is_(False), Course.is_deleted.is_(False),
                       Lesson.status != LessonStatus.CANCELLED,
                       Lesson.scheduled_at < end,
                       Lesson.scheduled_at + Lesson.duration_minutes * literal(timedelta(minutes=1)) > start)
                .order_by(Lesson.scheduled_at, Lesson.id))
        return list((await self.session.scalars(stmt)).all())
