"""Commit-free stages; caller holds schedule and recipient/domain prefix locks."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.integrations_vk.models import Booking, BookingEvent, BookingWindow
from src.modules.integrations_vk.booking_repository import BookingRepository
from src.modules.lessons.repository import LessonsRepository
from src.modules.teachers.models import Teacher


async def stage_lesson_with_snapshot(session: AsyncSession, booking: Booking,
                                     course_id: int, teacher_id: int, student_id: int) -> None:
    from src.modules.lessons.models import Lesson
    from src.modules.lesson_students.models import LessonStudent
    from src.modules.homework_placements.service import HomeworkPlacementsService
    if booking.lesson_id is not None:
        return
    lesson = Lesson(course_id=course_id, teacher_id=teacher_id, title='Занятие',
        scheduled_at=booking.start_at,
        duration_minutes=int((booking.end_at-booking.start_at).total_seconds() // 60),
        lesson_price_kopecks=booking.lesson_price_kopecks)
    session.add(lesson)
    await session.flush()
    session.add(LessonStudent(lesson_id=lesson.id, student_id=student_id))
    booking.lesson_id = lesson.id
    booking.revision += 1
    await session.flush()
    await HomeworkPlacementsService(session).recalculate_course(course_id, 'lesson_created')
    session.add(BookingEvent(booking_id=booking.id, kind='materialized', revision=booking.revision))


async def slot_busy(session: AsyncSession, teacher_user_id: int, start: datetime, end: datetime,
                    exclude_booking=None, exclude_lesson: int = 0) -> bool:
    repo = BookingRepository(session)
    teacher = await repo.one(Teacher, Teacher.user_id == teacher_user_id)
    return bool(await repo.overlaps(teacher_user_id, start, end, exclude_booking) or
                await LessonsRepository(session).overlapping_ids(teacher.id, start, end, exclude_lesson))


async def stage_cancel_booking(session: AsyncSession, booking: Booking, now: datetime) -> None:
    if booking.status == 'cancelled':
        return
    booking.status = 'cancelled'
    booking.revision += 1
    await session.flush()
    repo = BookingRepository(session)
    window = await repo.one(BookingWindow, BookingWindow.id == booking.window_id, lock=True)
    window.status = 'closed'
    window.revision += 1
    if (window.start_at > now and not window.withdrawn
            and not await repo.published_overlaps(window.teacher_user_id, window.start_at, window.end_at, window.id)
            and not await slot_busy(session, window.teacher_user_id, window.start_at, window.end_at,
                                    booking.id, booking.lesson_id or 0)):
        window.status = 'published'
    session.add(BookingEvent(booking_id=booking.id, kind='cancelled', revision=booking.revision))
