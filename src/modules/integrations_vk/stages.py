"""Commit-free F01.2 stages. Caller owns prefix locks and transaction.

No booking tables exist until F01.3; materialization accepts no pending bookings.
"""
from dataclasses import dataclass
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.courses.models import Course, AvatarCoursesType
from src.modules.students.models import Student
from src.modules.student_courses.models import StudentCourse
from src.modules.teacher_students.models import TeacherStudent
from src.modules.users.models import User, UserRole
from src.modules.integrations_vk.exception import IdentityError
from src.modules.integrations_vk.models import BookingRecipient


@dataclass(frozen=True)
class PrelockedWorkspace:
    teacher_id: int
    student_id: int | None
    course: Course | None
    pair: TeacherStudent | None


async def stage_create_inactive_student(session: AsyncSession, users: object,
                                        first_name: str, last_name: str, grade: int | None
                                        ) -> tuple[User, Student]:
    from src.modules.users.models_dto import RegisterUserRequestDTO
    if users.session_db is not session:
        raise RuntimeError('Identity stages require the same transaction session')
    user, student = await users.stage_create_inactive_account(RegisterUserRequestDTO(
        username='student-' + uuid4().hex, role=UserRole.STUDENT,
        first_name=first_name, last_name=last_name, school_grade=grade))
    await session.flush()
    return user, student


async def stage_link_student(session: AsyncSession, context: PrelockedWorkspace,
                             student: Student, allow_new: bool) -> TeacherStudent:
    pair = context.pair
    if pair is not None:
        if pair.ended_at is not None:
            raise IdentityError('ADMIN_LINK_REQUIRED')
        return pair
    if not allow_new:
        raise IdentityError('ADMIN_LINK_REQUIRED')
    pair = TeacherStudent(teacher_id=context.teacher_id, student_id=student.id)
    session.add(pair)
    await session.flush()
    return pair


async def stage_enroll(session: AsyncSession, course: Course, student: Student) -> StudentCourse:
    membership = StudentCourse(course_id=course.id, student_id=student.id)
    session.add(membership)
    await session.flush()
    return membership


async def stage_ensure_workspace(session: AsyncSession, context: PrelockedWorkspace,
                                 student: Student) -> Course:
    if context.course is not None:
        return context.course
    course = Course(teacher_id=context.teacher_id, name=f'{student.first_name} {student.last_name}',
                    slug='student-' + uuid4().hex, avatar_type=AvatarCoursesType.DEFAULT)
    session.add(course)
    await session.flush()
    await stage_enroll(session, course, student)
    return course


def stage_bind_recipient(recipient: BookingRecipient, user: User) -> None:
    if recipient.linked_student_user_id not in (None, user.id):
        raise IdentityError('IDENTITY_COLLISION')
    if recipient.linked_student_user_id is None:
        recipient.linked_student_user_id = user.id
        recipient.revision += 1


def stage_materialize(*, pending_bookings: tuple = ()) -> None:
    """F01.3 extension point; never silently drops work from a future caller."""
    if pending_bookings:
        raise IdentityError('REVIEW_REQUIRED')
