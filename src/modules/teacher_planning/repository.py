from typing import Any
from sqlalchemy import Select
from sqlalchemy.engine import RowMapping
from sqlalchemy.sql.selectable import Subquery
from datetime import date, datetime, timedelta, time
from zoneinfo import ZoneInfo
from sqlalchemy import select, func, literal, or_, and_, exists
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.base.repository_model import BaseRepository
from src.modules.teacher_planning.models_dto import NormRequestDTO
from src.modules.teacher_planning.models import WeeklyLessonNorm
from src.modules.lessons.models import Lesson, LessonStatus
from src.modules.lesson_students.models import LessonStudent
from src.modules.students.models import Student
from src.modules.teachers.models import Teacher
from src.modules.teacher_students.models import TeacherStudent
from src.modules.users.models import User, UserRole
from src.modules.courses.models import Course
from src.modules.student_courses.models import StudentCourse
from src.modules.lectures.models import Lecture
from src.modules.homeworks.models import Homework
from src.modules.homework_placements.models import HomeworkPlacement


def reminder_rows(teacher_user_id: int) -> Select:
    """One row per active recipient; shared SQL used by every aggregate/filter."""
    lecture = exists(select(Lecture.id).where(Lecture.lesson_student_id == LessonStudent.id))
    homework = exists(select(HomeworkPlacement.id).join(Homework, Homework.id == HomeworkPlacement.homework_id)
                      .where(HomeworkPlacement.lesson_student_id == LessonStudent.id))
    relevant = or_(Lesson.status == LessonStatus.COMPLETED,
                   Lesson.scheduled_at + Lesson.duration_minutes * literal(timedelta(minutes=1)) <= func.statement_timestamp())
    return (select(Lesson.id.label('lesson_id'), Student.user_id.label('student_user_id'),
                   Student.first_name, Student.last_name, Lesson.course_id, Course.name.label('course_name'),
                   Lesson.title, Lesson.scheduled_at,
                   homework.label('has_homework'), lecture.label('has_lecture'),
                   and_(relevant, ~homework, ~LessonStudent.homework_not_needed).label('needs_homework'),
                   and_(relevant, ~lecture, ~LessonStudent.lecture_not_needed).label('needs_lecture'),
                   LessonStudent.homework_not_needed, LessonStudent.lecture_not_needed)
            .join(LessonStudent, LessonStudent.lesson_id == Lesson.id)
            .join(Student, Student.id == LessonStudent.student_id)
            .join(User, User.id == Student.user_id)
            .join(Teacher, Teacher.id == Lesson.teacher_id).join(Course, Course.id == Lesson.course_id)
            .where(Teacher.user_id == teacher_user_id, Course.is_deleted.is_(False),
                   Lesson.is_deleted.is_(False), Lesson.status != LessonStatus.CANCELLED,
                   LessonStudent.access_ended_at.is_(None), User.is_active.is_(True),
                   exists(select(StudentCourse.id).where(
                       StudentCourse.course_id == Lesson.course_id,
                       StudentCourse.student_id == LessonStudent.student_id,
                       StudentCourse.is_deleted.is_(False), StudentCourse.history_revoked.is_(False),
                       StudentCourse.access_ended_at.is_(None),
                       StudentCourse.started_at <= func.statement_timestamp(),
                       or_(StudentCourse.expires_at.is_(None), StudentCourse.expires_at > func.statement_timestamp()),
                       exists(select(TeacherStudent.id).where(
                           TeacherStudent.teacher_id == Lesson.teacher_id,
                           TeacherStudent.student_id == LessonStudent.student_id,
                           TeacherStudent.ended_at.is_(None)).correlate(Lesson, LessonStudent))
                   ).correlate(Lesson, LessonStudent))))


def attention_counts(teacher_user_id: int) -> Subquery:
    rows = reminder_rows(teacher_user_id).subquery()
    return (select(rows.c.student_user_id,
                   func.count().filter(rows.c.needs_homework).label('missing_homework'),
                   func.count().filter(rows.c.needs_lecture).label('missing_lecture'))
            .group_by(rows.c.student_user_id).subquery())


class TeacherPlanningRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=WeeklyLessonNorm)

    async def linked_pair(self, teacher_user_id: int, student_user_id: int) -> TeacherStudent | None:
        return (await self.session.execute(select(TeacherStudent).join(Teacher).join(Student)
            .where(Teacher.user_id == teacher_user_id, Student.user_id == student_user_id,
                   TeacherStudent.ended_at.is_(None)).with_for_update(of=TeacherStudent))).scalar_one_or_none()

    async def norms(self, teacher_id: int, student_id: int, week: date) -> list[WeeklyLessonNorm]:
        return list((await self.session.scalars(select(WeeklyLessonNorm).where(
            WeeklyLessonNorm.teacher_id == teacher_id, WeeklyLessonNorm.student_id == student_id,
            WeeklyLessonNorm.week <= week).order_by(WeeklyLessonNorm.week, WeeklyLessonNorm.id))).all())

    async def write_norm(self, pair: TeacherStudent, data: NormRequestDTO) -> WeeklyLessonNorm:
        row = await self.session.scalar(select(WeeklyLessonNorm).where(
            WeeklyLessonNorm.teacher_id == pair.teacher_id, WeeklyLessonNorm.student_id == pair.student_id,
            WeeklyLessonNorm.week == data.week, WeeklyLessonNorm.kind == data.kind))
        if row is None:
            row = WeeklyLessonNorm(teacher_id=pair.teacher_id, student_id=pair.student_id,
                                   week=data.week, kind=data.kind)
            self.session.add(row)
        row.target, row.paused = data.target, data.paused
        await self.session.flush()
        return row

    async def students(self, teacher_user_id: int, week: date, q: str | None,
                       limit: int, offset: int, student_user_id: int | None = None, deficit_only: bool = False) -> tuple[list[RowMapping], list[WeeklyLessonNorm], int]:
        from src.modules.users.repository import UsersRepository
        start = datetime.combine(week, time(), ZoneInfo('Europe/Moscow'))
        count = (select(func.count(func.distinct(Lesson.id))).select_from(Lesson)
                 .join(LessonStudent, LessonStudent.lesson_id == Lesson.id)
                 .join(Course, Course.id == Lesson.course_id).join(Teacher, Teacher.id == Lesson.teacher_id)
                 .where(LessonStudent.student_id == Student.id, Teacher.user_id == teacher_user_id,
                        Lesson.scheduled_at >= start, Lesson.scheduled_at < start + timedelta(days=7),
                        Lesson.status != LessonStatus.CANCELLED, Lesson.is_deleted.is_(False),
                        Course.is_deleted.is_(False)).correlate(Student).scalar_subquery())
        counts = attention_counts(teacher_user_id)
        stmt = (select(User.id.label('user_id'), Student.id.label('student_id'), Teacher.id.label('teacher_id'),
                       User.username, Student.first_name, Student.last_name, TeacherStudent.planning_revision.label('norm_revision'), count.label('scheduled_count'),
                       func.coalesce(counts.c.missing_homework, 0).label('missing_homework'),
                       func.coalesce(counts.c.missing_lecture, 0).label('missing_lecture'))
                .join(Student, Student.user_id == User.id).join(TeacherStudent, TeacherStudent.student_id == Student.id)
                .join(Teacher, Teacher.id == TeacherStudent.teacher_id)
                .outerjoin(counts, counts.c.student_user_id == User.id)
                .where(Teacher.user_id == teacher_user_id, TeacherStudent.ended_at.is_(None), User.is_active.is_(True)))
        if deficit_only:
            from sqlalchemy import case
            def norm_value(column: Any) -> Any:
                return (select(column).where(WeeklyLessonNorm.teacher_id == Teacher.id,
                    WeeklyLessonNorm.student_id == Student.id, WeeklyLessonNorm.week <= week,
                    or_(WeeklyLessonNorm.kind == 'regular', WeeklyLessonNorm.week == week))
                    .order_by(case((WeeklyLessonNorm.kind == 'exception', 1), else_=0).desc(),
                              WeeklyLessonNorm.week.desc()).limit(1).correlate(Teacher, Student).scalar_subquery())
            stmt = stmt.where(count < norm_value(WeeklyLessonNorm.target),
                              norm_value(WeeklyLessonNorm.paused).is_(False))
        if student_user_id is not None:
            stmt = stmt.where(User.id == student_user_id)
        if q:
            stmt = stmt.where(UsersRepository.search_scope(q))
        filtered = stmt.cte('planning_students')
        total_query = select(func.count().label('total')).select_from(filtered).subquery()
        page = select(filtered).order_by(filtered.c.first_name, filtered.c.last_name, filtered.c.user_id).limit(limit).offset(offset).subquery()
        result = (await self.session.execute(select(page, total_query.c.total).select_from(
            total_query.outerjoin(page, literal(True))).order_by(page.c.first_name, page.c.last_name, page.c.user_id))).mappings().all()
        total = result[0]['total']
        rows = [r for r in result if r['user_id'] is not None]
        pairs = [r['student_id'] for r in rows]
        norms = list((await self.session.scalars(select(WeeklyLessonNorm).join(Teacher).where(
            Teacher.user_id == teacher_user_id, WeeklyLessonNorm.student_id.in_(pairs),
            WeeklyLessonNorm.week <= week).order_by(WeeklyLessonNorm.week, WeeklyLessonNorm.id))).all())
        return rows, norms, total

    async def reminders(self, teacher_user_id: int, lesson_id: int | None,
                        student_user_id: int | None, limit: int, offset: int, only_missing: bool) -> tuple[list[RowMapping], int]:
        rows = reminder_rows(teacher_user_id).subquery()
        stmt = select(rows)
        if lesson_id is not None:
            stmt = stmt.where(rows.c.lesson_id == lesson_id)
        if student_user_id is not None:
            stmt = stmt.where(rows.c.student_user_id == student_user_id)
        if only_missing:
            stmt = stmt.where(or_(rows.c.needs_homework, rows.c.needs_lecture))
        filtered = stmt.cte('recipient_reminders')
        total_query = select(func.count().label('total')).select_from(filtered).subquery()
        page = select(filtered).order_by(filtered.c.scheduled_at, filtered.c.lesson_id, filtered.c.student_user_id).limit(limit).offset(offset).subquery()
        result = (await self.session.execute(select(page, total_query.c.total).select_from(total_query.outerjoin(
            page, literal(True))).order_by(page.c.scheduled_at, page.c.lesson_id, page.c.student_user_id))).mappings().all()
        return [r for r in result if r['lesson_id'] is not None], result[0]['total']

    async def recipient(self, teacher_user_id: int, lesson_id: int, student_user_id: int) -> LessonStudent | None:
        return await self.session.scalar(select(LessonStudent).join(Lesson).join(Teacher)
            .join(Student, Student.id == LessonStudent.student_id).where(Teacher.user_id == teacher_user_id,
                Lesson.id == lesson_id, Student.user_id == student_user_id).with_for_update(of=LessonStudent))

    async def student_attention(self, teacher_user_id: int, ids: list[int]) -> dict[int, Any]:
        counts = attention_counts(teacher_user_id)
        return {r.student_user_id: r for r in (await self.session.execute(select(counts).where(counts.c.student_user_id.in_(ids)))).all()}

    async def weekly_earnings(self, teacher_user_id: int, week: date) -> RowMapping:
        start = datetime.combine(week, time.min, ZoneInfo('Europe/Moscow'))
        end = start + timedelta(days=7)
        from src.modules.check_permission.repository import lesson_active_scope
        # Match the active teacher calendar; archived lessons/courses are excluded.
        return (await self.session.execute(select(
            func.coalesce(func.sum(Lesson.lesson_price_kopecks).filter(
                Lesson.effective_status == LessonStatus.COMPLETED), 0).label('total_kopecks'),
            func.count(Lesson.id).label('lesson_count'),
            func.count(Lesson.id).filter(Lesson.effective_status == LessonStatus.COMPLETED).label('completed_count'),
            func.count(Lesson.id).filter((Lesson.effective_status == LessonStatus.COMPLETED) &
                Lesson.lesson_price_kopecks.is_(None)).label('unpriced_count')
        ).join(Teacher, Teacher.id == Lesson.teacher_id).where(
            Teacher.user_id == teacher_user_id, Lesson.scheduled_at >= start,
            Lesson.scheduled_at < end, Lesson.status != LessonStatus.CANCELLED,
            lesson_active_scope(teacher_user_id, UserRole.TEACHER)
        ))).mappings().one()
