from datetime import datetime
"""Shared SQL scopes. Lists and detail authorization use the same predicates."""
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy import exists, false, func, or_, and_, select, true
from src.modules.course_lifecycle.models import EnrollmentGap
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.courses.models import Course
from src.modules.lesson_students.models import LessonStudent
from src.modules.lessons.models import Lesson
from src.modules.student_courses.models import StudentCourse
from src.modules.students.models import Student
from src.modules.teacher_students.models import TeacherStudent
from src.modules.teachers.models import Teacher
from src.modules.users.models import User, UserRole


def profile_scope(user_id: int, role: UserRole) -> ColumnElement[bool]:
    if role == UserRole.ADMIN:
        return true()
    own = User.id == user_id
    if role == UserRole.TEACHER:
        linked = exists(select(TeacherStudent.id).join(Teacher).join(
            Student, Student.id == TeacherStudent.student_id
        ).where(Teacher.user_id == user_id, Student.user_id == User.id,
                TeacherStudent.ended_at.is_(None), User.role == UserRole.STUDENT).correlate(User))
    elif role == UserRole.STUDENT:
        linked = exists(select(TeacherStudent.id).join(Student).join(
            Teacher, Teacher.id == TeacherStudent.teacher_id
        ).where(Student.user_id == user_id, Teacher.user_id == User.id,
                TeacherStudent.ended_at.is_(None), User.role == UserRole.TEACHER).correlate(User))
    else:
        return false()
    return or_(own, linked)


def enrollment_time_scope(timestamp: ColumnElement[datetime]) -> ColumnElement[bool]:
    return and_(
        or_(StudentCourse.expires_at.is_(None), timestamp <= StudentCourse.expires_at),
        or_(StudentCourse.access_ended_at.is_(None), timestamp <= StudentCourse.access_ended_at),
        or_(StudentCourse.is_deleted.is_(False), StudentCourse.access_ended_at.is_not(None),
            and_(StudentCourse.deleted_at.is_not(None), timestamp <= StudentCourse.deleted_at)),
        ~exists(select(EnrollmentGap.id).where(
            EnrollmentGap.enrollment_id == StudentCourse.id,
            timestamp > EnrollmentGap.started_at, timestamp < EnrollmentGap.ended_at
        ).correlate(StudentCourse, timestamp.table)),
    )


def recipient_history_scope(timestamp: ColumnElement[datetime] | None = None) -> ColumnElement[bool]:
    """Use creation/publication time, never scheduled_at, for historical grants."""
    timestamp = LessonStudent.created_at if timestamp is None else timestamp
    return exists(select(StudentCourse.id).join(Lesson, Lesson.course_id == StudentCourse.course_id).where(
        Lesson.id == LessonStudent.lesson_id,
        StudentCourse.student_id == LessonStudent.student_id,
        StudentCourse.history_revoked.is_(False),
        enrollment_time_scope(LessonStudent.created_at), enrollment_time_scope(timestamp),
        ~exists(select(TeacherStudent.id).where(
            TeacherStudent.teacher_id == Lesson.teacher_id,
            TeacherStudent.student_id == StudentCourse.student_id,
            TeacherStudent.ended_at.is_not(None),
            or_(timestamp > TeacherStudent.ended_at, LessonStudent.created_at > TeacherStudent.ended_at)
        ).correlate(Lesson, StudentCourse, LessonStudent, timestamp.table)),
        or_(LessonStudent.access_ended_at.is_(None), timestamp <= LessonStudent.access_ended_at),
        or_(LessonStudent.access_ended_at.is_(None), LessonStudent.created_at <= LessonStudent.access_ended_at),
    ).correlate(LessonStudent, timestamp.table))


def material_scope(model: type, user_id: int, role: UserRole) -> ColumnElement[bool]:
    if role != UserRole.STUDENT:
        return true()
    return exists(select(LessonStudent.id).where(
        LessonStudent.id == model.lesson_student_id,
        recipient_scope(user_id, role), recipient_history_scope(model.created_at)
    ).correlate(model))


def submission_scope(model: type, user_id: int, role: UserRole) -> ColumnElement[bool]:
    if role != UserRole.STUDENT:
        return true()
    from src.modules.homeworks.models import Homework
    from src.modules.homework_submissions.models import HomeworkSubmission, HomeworkSubmissionFile
    if model is HomeworkSubmission:
        return exists(select(Homework.id).join(LessonStudent, LessonStudent.id == Homework.lesson_student_id).where(
            Homework.id == model.homework_id, material_scope(Homework, user_id, role),
            recipient_history_scope(model.created_at)).correlate(model))
    return exists(select(HomeworkSubmission.id).join(Homework).join(
        LessonStudent, LessonStudent.id == Homework.lesson_student_id).where(
            HomeworkSubmission.id == HomeworkSubmissionFile.submission_id,
            material_scope(Homework, user_id, role),
            recipient_history_scope(HomeworkSubmission.created_at),
            recipient_history_scope(HomeworkSubmissionFile.created_at)).correlate(HomeworkSubmissionFile))


def course_scope(user_id: int, role: UserRole) -> ColumnElement[bool]:
    if role == UserRole.ADMIN:
        return true()
    if role == UserRole.TEACHER:
        return exists(select(Teacher.id).where(Teacher.id == Course.teacher_id, Teacher.user_id == user_id).correlate(Course))
    if role == UserRole.STUDENT:
        return exists(select(StudentCourse.id).join(Student).where(
            StudentCourse.course_id == Course.id, Student.user_id == user_id,
            StudentCourse.history_revoked.is_(False)).correlate(Course))
    return false()


def lesson_scope(user_id: int, role: UserRole) -> ColumnElement[bool]:
    if role == UserRole.ADMIN:
        return true()
    if role == UserRole.TEACHER:
        return exists(select(Course.id).where(
            Course.id == Lesson.course_id, Course.teacher_id == Lesson.teacher_id,
            course_scope(user_id, role)).correlate(Lesson))
    if role == UserRole.STUDENT:
        return exists(select(LessonStudent.id).join(Student).where(
            LessonStudent.lesson_id == Lesson.id, Student.user_id == user_id,
            recipient_history_scope()).correlate(Lesson))
    return false()


def recipient_scope(user_id: int, role: UserRole) -> ColumnElement[bool]:
    if role == UserRole.STUDENT:
        return and_(exists(select(Student.id).where(
            Student.id == LessonStudent.student_id, Student.user_id == user_id).correlate(LessonStudent)),
            recipient_history_scope())
    return exists(select(Lesson.id).where(Lesson.id == LessonStudent.lesson_id, lesson_scope(user_id, role)).correlate(LessonStudent))


class PermissionRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=User)

    async def actor(self, user_id: int) -> User | None:
        return await self.session.scalar(select(User).where(User.id == user_id))

    async def visible(self, model: type[User] | type[Course] | type[Lesson], object_id: int, predicate: ColumnElement[bool]) -> bool:
        return await self.session.scalar(select(exists().where(model.id == object_id, predicate)))

    async def recipient(self, actor: User, lesson_id: int, student_user_id: int) -> LessonStudent | None:
        return await self.session.scalar(select(LessonStudent).join(Student).where(
            LessonStudent.lesson_id == lesson_id, Student.user_id == student_user_id,
            recipient_scope(actor.id, actor.role)))

    async def homework_recipient(self, homework_id: int, actor: User) -> LessonStudent | None:
        from src.modules.homeworks.models import Homework
        return await self.session.scalar(select(LessonStudent).join(
            Homework, Homework.lesson_student_id == LessonStudent.id
        ).where(Homework.id == homework_id, recipient_scope(actor.id, actor.role)))

    async def linked(self, teacher_user_id: int, student_user_id: int) -> bool:
        return await self.session.scalar(select(exists().where(
            TeacherStudent.teacher_id == Teacher.id, TeacherStudent.student_id == Student.id,
            Teacher.user_id == teacher_user_id, Student.user_id == student_user_id,
            TeacherStudent.ended_at.is_(None))))

    async def enrolled(self, course_id: int, student_user_id: int) -> bool:
        return await self.session.scalar(select(exists().where(
            StudentCourse.course_id == course_id, StudentCourse.student_id == Student.id,
            Student.user_id == student_user_id, StudentCourse.is_deleted.is_(False),
            StudentCourse.history_revoked.is_(False), StudentCourse.access_ended_at.is_(None),
            or_(StudentCourse.expires_at.is_(None), StudentCourse.expires_at > func.now()))))

    async def writable_course(self, course_id: int) -> bool:
        course = await self.session.scalar(select(Course).where(Course.id == course_id).with_for_update().execution_options(populate_existing=True))
        return course is not None and not course.is_deleted

    async def writable_lesson(self, lesson_id: int, check_participants: bool = True) -> bool:
        course_id = await self.session.scalar(select(Lesson.course_id).where(Lesson.id == lesson_id))
        if not await self.writable_course(course_id):
            return False
        lesson = await self.session.scalar(select(Lesson).where(Lesson.id == lesson_id).with_for_update().execution_options(populate_existing=True))
        if lesson is None or lesson.is_deleted:
            return False
        if not check_participants:
            return True
        recipients = list((await self.session.scalars(select(LessonStudent).where(
            LessonStudent.lesson_id == lesson_id).order_by(LessonStudent.id))).all())
        for recipient in recipients:
            if not await self.active_recipient(recipient, course_id):
                return False
        return True

    async def writable_recipient(self, recipient: LessonStudent) -> bool:
        if not await self.writable_lesson(recipient.lesson_id, check_participants=False):
            return False
        lesson = await self.session.get(Lesson, recipient.lesson_id)
        return await self.active_recipient(recipient, lesson.course_id)

    async def active_recipient(self, recipient: LessonStudent, course_id: int) -> bool:
        enrollment = await self.session.scalar(select(StudentCourse).where(
            StudentCourse.course_id == course_id,
            StudentCourse.student_id == recipient.student_id).with_for_update().execution_options(populate_existing=True))
        ended_teacher_link = await self.session.scalar(select(TeacherStudent.id).join(
            Course, Course.teacher_id == TeacherStudent.teacher_id).where(
                Course.id == course_id, TeacherStudent.student_id == recipient.student_id,
                TeacherStudent.ended_at.is_not(None)))
        now = await self.session.scalar(select(func.clock_timestamp()))
        return bool(enrollment and not enrollment.is_deleted and not enrollment.history_revoked
                    and enrollment.access_ended_at is None and ended_teacher_link is None
                    and (enrollment.expires_at is None or enrollment.expires_at > now)
                    and recipient.access_ended_at is None)

    async def material_visible(self, model: type, object_id: int, actor: User) -> bool:
        return bool(await self.session.scalar(select(exists().where(
            model.id == object_id, material_scope(model, actor.id, actor.role)))))


def active_enrollment_scope(course_id: ColumnElement[int], student_user_id: int) -> ColumnElement[bool]:
    """Current participation is separate from the historical read grant."""
    from sqlalchemy.orm import aliased
    owner_course = aliased(Course)
    return exists(select(StudentCourse.id).join(Student).join(
        owner_course, owner_course.id == StudentCourse.course_id).where(
        StudentCourse.course_id == course_id, Student.user_id == student_user_id,
        StudentCourse.is_deleted.is_(False), StudentCourse.history_revoked.is_(False),
        StudentCourse.access_ended_at.is_(None), StudentCourse.started_at <= func.statement_timestamp(),
        or_(StudentCourse.expires_at.is_(None), StudentCourse.expires_at > func.statement_timestamp()),
        exists(select(TeacherStudent.id).where(
            TeacherStudent.teacher_id == owner_course.teacher_id,
            TeacherStudent.student_id == StudentCourse.student_id,
            TeacherStudent.ended_at.is_(None)).correlate(owner_course, StudentCourse)),
    ).correlate(course_id.table))


def course_active_scope(user_id: int, role: UserRole) -> ColumnElement[bool]:
    active = Course.is_deleted.is_(False)
    if role == UserRole.STUDENT:
        active = and_(active, active_enrollment_scope(Course.id, user_id))
    return active


def lesson_active_scope(user_id: int, role: UserRole) -> ColumnElement[bool]:
    active = and_(Lesson.is_deleted.is_(False), exists(select(Course.id).where(
        Course.id == Lesson.course_id, Course.is_deleted.is_(False)).correlate(Lesson)))
    if role == UserRole.STUDENT:
        active = and_(active, active_enrollment_scope(Lesson.course_id, user_id),
            exists(select(LessonStudent.id).join(Student).where(
                LessonStudent.lesson_id == Lesson.id, Student.user_id == user_id,
                LessonStudent.access_ended_at.is_(None), recipient_history_scope()).correlate(Lesson)))
    return active


def course_student_filter(student_user_id: int) -> ColumnElement[bool]:
    return exists(select(StudentCourse.id).join(Student).where(
        StudentCourse.course_id == Course.id, Student.user_id == student_user_id).correlate(Course))


def lesson_student_filter(student_user_id: int) -> ColumnElement[bool]:
    return exists(select(LessonStudent.id).join(Student).where(
        LessonStudent.lesson_id == Lesson.id, Student.user_id == student_user_id).correlate(Lesson))


class ReadContextRepository:
    """Bounded, column-only context reads; no locks, flushes or writes on GET."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def recipients(self, ids: list[int]) -> dict[int, dict]:
        rows = (await self.session.execute(select(
            LessonStudent.id, LessonStudent.lesson_id, LessonStudent.access_ended_at.label('recipient_ended'),
            Student.user_id.label('student_user_id'), Student.first_name, Student.last_name, Student.school_grade, User.username,
            Lesson.course_id, Lesson.title.label('lesson_title'), Lesson.is_deleted.label('lesson_archived'),
            Course.name.label('course_name'), Course.is_deleted.label('course_archived'),
            Teacher.user_id.label('teacher_user_id'), StudentCourse.id.label('enrollment_id'),
            StudentCourse.is_deleted.label('enrollment_deleted'), StudentCourse.history_revoked,
            StudentCourse.access_ended_at.label('enrollment_ended'), StudentCourse.started_at,
            StudentCourse.expires_at, TeacherStudent.ended_at.label('link_ended'),
            func.statement_timestamp().label('now'),
        ).join(Student, Student.id == LessonStudent.student_id).join(User, User.id == Student.user_id)
          .join(Lesson, Lesson.id == LessonStudent.lesson_id).join(Course, Course.id == Lesson.course_id)
          .join(Teacher, Teacher.id == Course.teacher_id)
          .outerjoin(StudentCourse, and_(StudentCourse.course_id == Course.id, StudentCourse.student_id == Student.id))
          .outerjoin(TeacherStudent, and_(TeacherStudent.teacher_id == Teacher.id, TeacherStudent.student_id == Student.id))
          .where(LessonStudent.id.in_(ids)))).mappings().all()
        return {r['id']: dict(r) for r in rows}

    async def lesson_recipients(self, actor: User, lesson_ids: list[int]) -> list[int]:
        return list((await self.session.scalars(select(LessonStudent.id).where(
            LessonStudent.lesson_id.in_(lesson_ids), recipient_scope(actor.id, actor.role))
            .order_by(LessonStudent.id))).all())

    async def course_states(self, actor: User, ids: list[int]) -> list:
        # Active enrollment uses the very same read view predicate as T14a.
        return (await self.session.execute(select(Course.id, Course.is_deleted,
            course_active_scope(actor.id, actor.role).label('active')).where(Course.id.in_(ids)))).all()

    async def course_student_states(self, actor: User, ids: list[int]) -> list:
        return (await self.session.execute(select(
            StudentCourse.course_id, StudentCourse.is_deleted, StudentCourse.history_revoked,
            StudentCourse.access_ended_at, StudentCourse.expires_at, StudentCourse.started_at,
            TeacherStudent.ended_at, func.statement_timestamp()).select_from(StudentCourse).join(Student)
            .join(Course, Course.id == StudentCourse.course_id).outerjoin(TeacherStudent, and_(
                TeacherStudent.teacher_id == Course.teacher_id, TeacherStudent.student_id == Student.id))
            .where(StudentCourse.course_id.in_(ids), Student.user_id == actor.id))).all()


    async def lesson_states(self, ids: list[int]) -> dict:
        rows = (await self.session.execute(select(Lesson.id, Lesson.is_deleted,
            Course.is_deleted.label('course_archived'),
            select(func.count(LessonStudent.id)).where(LessonStudent.lesson_id == Lesson.id)
                .correlate(Lesson).scalar_subquery().label('recipients'))
            .join(Course, Course.id == Lesson.course_id).where(Lesson.id.in_(ids)))).all()
        return {r.id: r for r in rows}

    async def creatable_courses(self, ids: list[int]) -> set[int]:
        rows = await self.session.scalars(select(Course.id).where(Course.id.in_(ids),
            Course.is_deleted.is_(False), exists(select(StudentCourse.id)
                .join(Student, Student.id == StudentCourse.student_id).join(User, User.id == Student.user_id).where(
                User.is_active.is_(True), User.role == UserRole.STUDENT,
                StudentCourse.started_at <= func.statement_timestamp(),
                StudentCourse.course_id == Course.id, StudentCourse.is_deleted.is_(False),
                StudentCourse.history_revoked.is_(False), StudentCourse.access_ended_at.is_(None),
                or_(StudentCourse.expires_at.is_(None), StudentCourse.expires_at > func.statement_timestamp()),
                exists(select(TeacherStudent.id).where(TeacherStudent.teacher_id == Course.teacher_id,
                    TeacherStudent.student_id == StudentCourse.student_id, TeacherStudent.ended_at.is_(None))
                    .correlate(Course, StudentCourse))))
        ))
        return set(rows.all())
