"""Booking SQL; transaction ownership stays in services."""
from datetime import datetime
from uuid import UUID
from sqlalchemy import select
from src.modules.integrations_vk.repository import IdentityRepository
from src.modules.integrations_vk.models import Booking, BookingWindow


class BookingRepository(IdentityRepository):
    async def overlaps(self, teacher_user_id: int, start: datetime, end: datetime,
                       exclude_booking: UUID | None = None) -> list[Booking]:
        predicates = [Booking.teacher_user_id == teacher_user_id, Booking.status == 'confirmed',
                      Booking.lesson_id.is_(None), Booking.start_at < end, Booking.end_at > start]
        if exclude_booking is not None:
            predicates.append(Booking.id != exclude_booking)
        return await self.rows(Booking, *predicates)

    async def published_overlaps(self, teacher: int, start: datetime, end: datetime,
                                 exclude: UUID | None = None) -> list[BookingWindow]:
        predicates = [BookingWindow.teacher_user_id == teacher, BookingWindow.status == 'published',
                      BookingWindow.start_at < end, BookingWindow.end_at > start]
        if exclude is not None:
            predicates.append(BookingWindow.id != exclude)
        return await self.rows(BookingWindow, *predicates)

    async def course_references(self, course_id: int) -> bool:
        from src.modules.lessons.models import Lesson
        return bool(await self.session.scalar(select(Booking.id).join(Lesson, Lesson.id == Booking.lesson_id)
            .where(Lesson.course_id == course_id).limit(1)))

    async def windows_page(self, teacher: int, connection: UUID, week, cursor: UUID | None, limit: int, published_only: bool = False):
        predicates = [BookingWindow.teacher_user_id == teacher, BookingWindow.connection_id == connection,
                      BookingWindow.week_start == week]
        if published_only: predicates.append(BookingWindow.status == 'published')
        if cursor is not None: predicates.append(BookingWindow.id > cursor)
        return list((await self.session.scalars(select(BookingWindow).where(*predicates)
            .order_by(BookingWindow.id).limit(limit+1))).all())

    async def bookings_page(self, teacher: int, connection: UUID, week, cursor: UUID | None, limit: int):
        predicates = [Booking.teacher_user_id == teacher, Booking.connection_id == connection,
                      BookingWindow.week_start == week]
        if cursor is not None: predicates.append(Booking.id > cursor)
        return list((await self.session.scalars(select(Booking).join(BookingWindow,
            BookingWindow.id == Booking.window_id).where(*predicates).order_by(Booking.id).limit(limit+1))).all())


    async def calendar_page(self, teacher: int, start, end, limit: int):
        from sqlalchemy import func
        from src.modules.lessons.models import Lesson
        at = func.coalesce(Lesson.scheduled_at, Booking.start_at)
        return list((await self.session.scalars(select(Booking).outerjoin(Lesson, Lesson.id == Booking.lesson_id)
            .where(Booking.teacher_user_id == teacher, at >= start, at < end,
                   Booking.status == 'confirmed').order_by(Booking.id).limit(limit+1))).all())

    async def linked_page(self, teacher: int, connection: UUID, student_user_id: int,
                          cursor: UUID | None, limit: int):
        from src.modules.integrations_vk.models import BookingRecipient
        predicates = [Booking.teacher_user_id == teacher, Booking.connection_id == connection,
                      BookingRecipient.linked_student_user_id == student_user_id]
        if cursor is not None: predicates.append(Booking.id > cursor)
        return list((await self.session.scalars(select(Booking).join(BookingRecipient,
            BookingRecipient.id == Booking.recipient_id).where(*predicates)
            .order_by(Booking.id).limit(limit+1))).all())
