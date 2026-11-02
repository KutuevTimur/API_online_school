"""Local booking transaction owner. No transport credentials or external effects."""
import secrets
from datetime import UTC, date, datetime, timedelta
from typing import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID, uuid4
from src.modules.integrations_vk.service import IdentityService, digest, RetryDiscovery
from src.modules.integrations_vk.booking_repository import BookingRepository
from src.modules.integrations_vk.booking_stages import slot_busy, stage_lesson_with_snapshot, stage_cancel_booking
from src.modules.integrations_vk.models import (Booking, BookingWindow, BookingInteraction, BookingEvent,
    BookingRecipient, ExternalContact, ExternalIdentityLink, ParentGrant, IdentityOperation, VkActorContext)
from src.modules.integrations_vk.models_dto import (CloseWindowsRequest, OperationResult, WindowView, BookingView,
    PublishWindowsRequest, RevisionRequest, PrepareBookingRequest, ConfirmBookingRequest,
    MaterializeRequest, BookingResolveRequest, ResolveResponse, WindowsPage, BookingsPage)
from src.modules.integrations_vk.exception import IdentityError
from src.modules.users.models import UserRole
from src.modules.teachers.models import Teacher
from src.modules.students.models import Student
from src.modules.courses.models import Course
from src.modules.teacher_students.models import TeacherStudent
from src.modules.audit_events.service import AuditEventsService


class BookingService(IdentityService):
    def __init__(self, session: AsyncSession, users=None, clock: Callable = lambda: datetime.now(UTC)) -> None:
        super().__init__(session, users, clock)
        self.repo = BookingRepository(self.session)

    async def teacher(self, actor: int, connection: UUID) -> Teacher:
        user = await self.user(actor, activated=True)
        await self.connection(connection)
        if user.role != UserRole.TEACHER or actor not in await self.repo.teachers(connection):
            raise IdentityError('NOT_FOUND', 404)
        return await self.repo.one(Teacher, Teacher.user_id == actor)

    async def publish(self, actor: int, data: PublishWindowsRequest) -> OperationResult:
        await self.teacher(actor, data.connection_id)
        async def work() -> tuple[dict, dict]:
            await self.repo.schedules([actor])
            await self.teacher(actor, data.connection_id)
            for item in data.items:
                if item.start_at <= self.clock() or await self.repo.published_overlaps(actor, item.start_at, item.end_at) or await slot_busy(self.session, actor, item.start_at, item.end_at):
                    raise IdentityError('SLOT_UNAVAILABLE')
                self.repo.stage(BookingWindow, connection_id=data.connection_id, teacher_user_id=actor,
                    week_start=data.week_start, start_at=item.start_at, end_at=item.end_at, created_by=actor)
                await self.session.flush()
            rows = await self.repo.rows(BookingWindow, BookingWindow.teacher_user_id == actor,
                BookingWindow.connection_id == data.connection_id, BookingWindow.week_start == data.week_start)
            # Return exactly this batch, including when the week already has other windows.
            refs = [str(r.id) for r in rows if any(r.start_at == i.start_at and r.end_at == i.end_at for i in data.items) and r.status == 'published']
            return {'kind': 'windows_published', 'window_ids': refs}, {}
        return (await self._operation(data.connection_id, 'windows_publish', data.operation_id,
            data.model_dump(exclude={'operation_id'}), work, user_id=actor))[0]

    async def close(self, actor: int, id: UUID, data: RevisionRequest) -> OperationResult:
        row = await self.repo.one(BookingWindow, BookingWindow.id == id, BookingWindow.teacher_user_id == actor)
        if row is None: raise IdentityError('NOT_FOUND', 404)
        connection = row.connection_id
        await self.teacher(actor, connection)
        async def work() -> tuple[dict, dict]:
            await self.repo.schedules([actor])
            current = await self.repo.scoped(BookingWindow, connection, id, lock=True)
            if current.revision != data.expected_revision: raise IdentityError('STALE_REVISION')
            current.withdrawn = True
            if current.status != 'consumed': current.status = 'closed'
            current.revision += 1
            return {'kind': 'window_closed', 'window_ids': [str(id)]}, {}
        return (await self._operation(connection, 'window_close', data.operation_id,
            {'window': id, **data.model_dump(exclude={'operation_id'})}, work, user_id=actor))[0]

    async def authorize_recipient(self, context: VkActorContext, recipient: BookingRecipient | None,
                                  teacher: int, *, lock: bool = False) -> ParentGrant | None:
        if recipient is None or recipient.connection_id != context.connection_id or teacher not in await self.repo.recipient_teachers(recipient.id):
            raise IdentityError('NOT_FOUND', 404)
        if context.contact_id == recipient.child_contact_id:
            return None
        grant = await self.repo.one(ParentGrant, ParentGrant.connection_id == context.connection_id,
            ParentGrant.parent_contact_id == context.contact_id, ParentGrant.recipient_id == recipient.id,
            ParentGrant.teacher_user_id == teacher, lock=lock)
        if grant is None: raise IdentityError('NOT_FOUND', 404)
        if grant.state != 'confirmed': raise IdentityError('GRANT_PENDING' if grant.state == 'pending' else 'GRANT_REVOKED')
        return grant

    async def prepare(self, data: PrepareBookingRequest) -> dict:
        try:
            context = await self.actor_context(data.actor_context)
            window = await self.repo.scoped(BookingWindow, context.connection_id, data.window_id)
            if window is None: raise IdentityError('NOT_FOUND', 404)
            recipient = await self.lock_recipient(context.connection_id, data.recipient_id, context.contact_id)
            await self.authorize_recipient(context, recipient, window.teacher_user_id)
            if window.status != 'published' or window.revision != data.expected_revision or window.start_at <= self.clock():
                raise IdentityError('STALE_REVISION')
            previous = await self.repo.rows(BookingInteraction, BookingInteraction.actor_contact_id == context.contact_id,
                BookingInteraction.window_id == window.id, BookingInteraction.recipient_id == recipient.id, lock=True)
            for old in previous:
                old.expires_at = min(old.expires_at, self.clock())
            secret, operation, expires = secrets.token_urlsafe(32), uuid4(), self.clock()+timedelta(minutes=10)
            self.repo.stage(BookingInteraction, connection_id=context.connection_id,
                actor_contact_id=context.contact_id, recipient_id=recipient.id, window_id=window.id,
                window_revision=window.revision, digest=digest(secret), operation_id=operation, expires_at=expires)
            await self.session.commit()
            return {'handle': secret, 'operation_id': operation, 'expires_at': expires}
        except Exception:
            await self.session.rollback(); raise

    async def confirm_booking(self, data: ConfirmBookingRequest) -> OperationResult:
        context = await self.actor_context(data.actor_context)
        interaction = await self.repo.one(BookingInteraction, BookingInteraction.connection_id == context.connection_id,
            BookingInteraction.digest == digest(data.handle), BookingInteraction.actor_contact_id == context.contact_id)
        if interaction is None or interaction.operation_id != data.operation_id: raise IdentityError('NOT_FOUND', 404)
        connection, recipient_id, window_id = context.connection_id, interaction.recipient_id, interaction.window_id
        discovered_window = await self.repo.scoped(BookingWindow, connection, window_id)
        teacher_id = discovered_window.teacher_user_id
        interaction_id, contact_id = interaction.id, context.contact_id
        async def work() -> tuple[dict, dict]:
            await self.repo.schedules([teacher_id])
            recipient = await self.lock_recipient(connection, recipient_id, contact_id)
            fresh_context = await self.actor_context(data.actor_context)
            grant = await self.authorize_recipient(fresh_context, recipient, teacher_id, lock=True)
            handle = await self.repo.scoped(BookingInteraction, connection, interaction_id, lock=True)
            window = await self.repo.scoped(BookingWindow, connection, window_id, lock=True)
            if handle.expires_at <= self.clock(): raise IdentityError('HANDLE_EXPIRED', 410)
            if handle.window_revision != data.expected_revision or window.revision != data.expected_revision: raise IdentityError('STALE_REVISION')
            if window.status != 'published' or window.start_at <= self.clock() or await slot_busy(self.session, teacher_id, window.start_at, window.end_at):
                raise IdentityError('SLOT_UNAVAILABLE')
            workspace = await self.materialization_context(teacher_id, recipient, required=False)
            price = workspace[2].lesson_price_kopecks if workspace else None
            booking = self.repo.stage(Booking, connection_id=connection, window_id=window.id,
                teacher_user_id=teacher_id, recipient_id=recipient.id, actor_contact_id=contact_id,
                parent_grant_id=grant.id if grant else None, parent_grant_revision=grant.revision if grant else None,
                start_at=window.start_at, end_at=window.end_at, lesson_price_kopecks=price)
            window.status = 'consumed'; window.revision += 1
            await self.session.flush()
            if workspace:
                teacher, student, pair, course = workspace
                await stage_lesson_with_snapshot(self.session, booking, course.id, teacher.id, student.id)
            self.repo.stage(BookingEvent, booking_id=booking.id, kind='confirmed', revision=1)
            AuditEventsService(self.session).stage(teacher_id, 'vk_booking_confirm', 'teacher', teacher_id)
            return {'kind': 'booking_confirmed', 'booking_id': str(booking.id), 'lesson_id': booking.lesson_id}, {}
        return (await self._operation(connection, 'booking_confirm', data.operation_id,
            {'handle_digest': digest(data.handle), 'expected_revision': data.expected_revision}, work,
            contact_id=contact_id))[0]

    async def lock_recipient(self, connection: UUID, id: UUID, actor_contact: UUID | None = None) -> BookingRecipient:
        recipient = await self.repo.scoped(BookingRecipient, connection, id)
        if recipient is None: raise IdentityError('NOT_FOUND', 404)
        contacts = sorted({recipient.child_contact_id, *([actor_contact] if actor_contact else [])})
        for contact in contacts:
            await self.repo.scoped(ExternalContact, connection, contact, lock=True)
        current = await self.repo.scoped(BookingRecipient, connection, id, lock=True)
        await self.repo.rows(ExternalIdentityLink, ExternalIdentityLink.contact_id == current.child_contact_id,
            ExternalIdentityLink.revoked_at.is_(None), lock=True)
        return current

    async def materialization_context(self, actor: int, recipient: BookingRecipient, *,
                                      required: bool) -> tuple[Teacher, Student, TeacherStudent, Course] | None:
        """Acquire explicit course/pair/membership/User levels before staged inserts."""
        from src.modules.courses.workspace_lock import lock_workspace_pair
        from src.modules.teacher_students.repository import TeacherStudentRepository
        from src.modules.integrations_vk.stages import PrelockedWorkspace, stage_ensure_workspace
        teacher = await self.teacher(actor, recipient.connection_id)
        student = await self.repo.one(Student, Student.user_id == recipient.linked_student_user_id) if recipient.linked_student_user_id else None
        if student is None:
            if required: raise IdentityError('REVIEW_REQUIRED')
            return None
        links = await self.repo.rows(ExternalIdentityLink, ExternalIdentityLink.contact_id == recipient.child_contact_id,
            ExternalIdentityLink.user_id == student.user_id, ExternalIdentityLink.purpose == 'student', ExternalIdentityLink.revoked_at.is_(None), lock=True)
        if not links:
            if required: raise IdentityError('REVIEW_REQUIRED')
            return None
        await lock_workspace_pair(self.session, teacher.id, student.id)
        pairs = TeacherStudentRepository(self.session)
        course_ids = await pairs.lock_courses(teacher.id, student.id)
        pair = await pairs.previous_link(teacher.id, student.id)
        await pairs.memberships(teacher.id, student.id)
        for user_id in sorted({actor, student.user_id}):
            await self.user(user_id, lock=True, activated=user_id == actor)
        if pair is None or pair.ended_at is not None:
            if required: raise IdentityError('ADMIN_LINK_REQUIRED')
            return None
        candidates = await self.repo.workspace_candidates(teacher.id, student.id, eligible=True)
        if any(c.id not in course_ids for c in candidates): raise RetryDiscovery()
        if len(candidates) > 1 or (not candidates and await self.repo.workspace_candidates(teacher.id, student.id, eligible=False)):
            raise IdentityError('COURSE_NOT_WRITABLE')
        course = candidates[0] if candidates else await stage_ensure_workspace(self.session,
            PrelockedWorkspace(teacher.id, student.id, None, pair), student)
        return teacher, student, pair, course

    async def owned_booking(self, actor: int, id: UUID) -> Booking:
        row = await self.repo.one(Booking, Booking.id == id, Booking.teacher_user_id == actor)
        if row is None: raise IdentityError('NOT_FOUND', 404)
        await self.teacher(actor, row.connection_id)
        return row

    async def materialize(self, actor: int, id: UUID, data: MaterializeRequest) -> OperationResult:
        discovered = await self.owned_booking(actor, id)
        connection, recipient_id = discovered.connection_id, discovered.recipient_id
        window_id = discovered.window_id
        async def work() -> tuple[dict, dict]:
            teachers = await self.repo.recipient_teachers(recipient_id)
            await self.repo.schedules(teachers)
            recipient = await self.lock_recipient(connection, recipient_id)
            if teachers != await self.repo.recipient_teachers(recipient_id): raise RetryDiscovery()
            rows = await self.repo.rows(Booking, Booking.recipient_id == recipient_id,
                Booking.teacher_user_id == actor, Booking.status == 'confirmed', lock=True)
            current = next((r for r in rows if r.id == id), None)
            if current is None or current.revision != data.expected_revision or recipient.revision != data.expected_recipient_revision:
                raise IdentityError('STALE_REVISION')
            pending = [r for r in rows if r.lesson_id is None]
            if any(r.start_at <= self.clock() for r in pending) and not data.review_past: raise IdentityError('REVIEW_REQUIRED')
            teacher, student, pair, course = await self.materialization_context(actor, recipient, required=True)
            for booking in pending:
                await stage_lesson_with_snapshot(self.session, booking, course.id, teacher.id, student.id)
            AuditEventsService(self.session).stage(actor, 'vk_booking_materialize', 'teacher', actor)
            return {'kind': 'materialized', 'booking_id': str(id), 'lesson_id': current.lesson_id}, {}
        return (await self._operation(connection, 'booking_materialize', data.operation_id,
            {'booking': id, **data.model_dump(exclude={'operation_id'})}, work, user_id=actor))[0]

    async def cancel(self, actor: int, id: UUID, data: RevisionRequest) -> OperationResult:
        """Teacher domain port; request/approval transport belongs to F01.5."""
        discovered = await self.owned_booking(actor, id)
        connection, recipient_id = discovered.connection_id, discovered.recipient_id
        window_id = discovered.window_id
        async def work() -> tuple[dict, dict]:
            await self.repo.schedules([actor])
            await self.lock_recipient(connection, recipient_id)
            await self.repo.one(BookingWindow, BookingWindow.id == window_id, lock=True)
            booking = await self.repo.scoped(Booking, connection, id, lock=True)
            if booking.revision != data.expected_revision: raise IdentityError('STALE_REVISION')
            if booking.lesson_id is not None:
                from src.modules.lessons.models import Lesson, LessonStatus
                from src.modules.courses.models import Course
                from src.modules.homework_placements.service import HomeworkPlacementsService
                lesson = await self.repo.one(Lesson, Lesson.id == booking.lesson_id)
                await self.repo.one(Course, Course.id == lesson.course_id, lock=True)
                lesson = await self.repo.one(Lesson, Lesson.id == lesson.id, lock=True)
                lesson.status = LessonStatus.CANCELLED
                await self.session.flush()
                await HomeworkPlacementsService(self.session).recalculate_course(lesson.course_id, 'lesson_updated')
            await stage_cancel_booking(self.session, booking, self.clock())
            return {'kind': 'cancel_approved', 'booking_id': str(id), 'lesson_id': booking.lesson_id}, {}
        return (await self._operation(connection, 'booking_cancel', data.operation_id,
            {'booking': id, **data.model_dump(exclude={'operation_id'})}, work, user_id=actor))[0]

    async def booking_view(self, actor: int, id: UUID) -> BookingView:
        row = await self.owned_booking(actor, id)
        recipient = await self.repo.scoped(BookingRecipient, row.connection_id, row.recipient_id)
        access = 'unresolved'
        if recipient.linked_student_user_id:
            from src.modules.users.models import User
            user = await self.repo.one(User, User.id == recipient.linked_student_user_id)
            access = 'blocked' if not user.is_active else 'active' if user.is_activated else 'inactive'
            student = await self.repo.one(Student, Student.user_id == user.id)
            teacher = await self.repo.one(Teacher, Teacher.user_id == actor)
            pair = await self.repo.one(TeacherStudent, TeacherStudent.teacher_id == teacher.id,
                TeacherStudent.student_id == student.id) if student else None
            if user.is_active and (pair is None or pair.ended_at is not None): access = 'awaiting_admin_link'
            if row.lesson_id is not None:
                from src.modules.lessons.models import Lesson
                lesson = await self.repo.one(Lesson, Lesson.id == row.lesson_id)
                course = await self.repo.one(Course, Course.id == lesson.course_id)
                if lesson.is_deleted or course.is_deleted: access = 'blocked'
        if row.start_at <= self.clock() and row.lesson_id is None: access = 'review_required'
        return BookingView(booking_id=row.id, revision=row.revision, start_at=row.start_at, end_at=row.end_at,
            status=row.status, recipient={'recipient_id': str(recipient.id), 'first_name': recipient.first_name,
            'last_name': recipient.last_name, 'grade': recipient.grade, 'revision': recipient.revision,
            'linked_student_user_id': recipient.linked_student_user_id,
            'parent_grants': await self.parent_grants(actor, recipient)}, lesson_id=row.lesson_id,
            access_state=access, lesson_price_kopecks=row.lesson_price_kopecks)

    async def connector_receipt(self, actor_context: str, operation_id: UUID) -> OperationResult:
        context = await self.actor_context(actor_context)
        row = await self.repo.one(IdentityOperation, IdentityOperation.connection_id == context.connection_id,
            IdentityOperation.actor_contact_id == context.contact_id, IdentityOperation.operation_id == operation_id)
        if row is None: raise IdentityError('NOT_FOUND', 404)
        return OperationResult(operation_id=operation_id, state=row.state, result=row.result,
            error={'code': row.error_code, 'retryable': False} if row.error_code else None)

    async def prelock_lesson_booking(self, actor: int, lesson_id: int) -> Booking | None:
        booking = await self.repo.one(Booking, Booking.lesson_id == lesson_id, Booking.teacher_user_id == actor)
        if booking is None: return None
        await self.lock_recipient(booking.connection_id, booking.recipient_id)
        await self.repo.one(BookingWindow, BookingWindow.id == booking.window_id, lock=True)
        return await self.repo.one(Booking, Booking.id == booking.id, lock=True)

    async def resolve_booking(self, actor: int, id: UUID, data: BookingResolveRequest) -> ResolveResponse:
        from src.modules.integrations_vk.models_dto import ResolveRecipientRequest
        booking = await self.owned_booking(actor, id)
        return await self.resolve_invite(actor, booking.recipient_id, ResolveRecipientRequest(
            operation_id=data.operation_id, expected_revision=data.expected_recipient_revision,
            mode=data.mode, student_user_id=data.student_user_id), booking_id=id, booking_data=data)

    @staticmethod
    def validate_page(week: date, limit: int) -> None:
        if week.weekday() != 0 or not 1 <= limit <= 100:
            raise IdentityError('INVALID_REQUEST', 422)

    async def list_windows(self, actor: int, connection: UUID, week: date,
                           cursor: UUID | None = None, limit: int = 25, published_only: bool = False) -> WindowsPage:
        self.validate_page(week, limit)
        await self.teacher(actor, connection)
        rows = await self.repo.windows_page(actor, connection, week, cursor, limit, published_only)
        return WindowsPage(items=[WindowView(window_id=r.id, revision=r.revision, start_at=r.start_at,
            end_at=r.end_at, status=r.status) for r in rows[:limit]],
            next_cursor=rows[limit-1].id if len(rows)>limit else None)

    async def list_bookings(self, actor: int, connection: UUID, week: date,
                            cursor: UUID | None = None, limit: int = 25) -> BookingsPage:
        self.validate_page(week, limit)
        await self.teacher(actor, connection)
        rows = await self.repo.bookings_page(actor, connection, week, cursor, limit)
        return BookingsPage(items=[await self.booking_view(actor, r.id) for r in rows[:limit]],
            next_cursor=rows[limit-1].id if len(rows)>limit else None)

    async def available_windows(self, actor_context: str, teacher: int, week: date) -> list[WindowView]:
        self.validate_page(week, 100)
        context = await self.actor_context(actor_context)
        if teacher not in await self.repo.teachers(context.connection_id): raise IdentityError('NOT_FOUND', 404)
        rows = await self.repo.windows_page(teacher, context.connection_id, week, None, 100)
        return [WindowView(window_id=r.id, revision=r.revision, start_at=r.start_at, end_at=r.end_at,
            status=r.status) for r in rows[:100] if r.status == 'published' and r.start_at > self.clock()
            and not await slot_busy(self.session, teacher, r.start_at, r.end_at)]


    async def parent_grants(self, actor: int, recipient: BookingRecipient) -> list[dict]:
        grants = await self.repo.rows(ParentGrant, ParentGrant.connection_id == recipient.connection_id,
            ParentGrant.recipient_id == recipient.id, ParentGrant.teacher_user_id == actor)
        result = []
        for grant in grants:
            contact = await self.repo.scoped(ExternalContact, recipient.connection_id, grant.parent_contact_id)
            result.append({'grant_id': grant.id, 'revision': grant.revision, 'state': grant.state,
                'parent_label': 'Родитель · …' + contact.subject[-2:]})
        return result


    async def calendar(self, actor: int, week: date) -> BookingsPage:
        self.validate_page(week, 100)
        user = await self.user(actor, activated=True)
        if user.role != UserRole.TEACHER:
            raise IdentityError('SCOPE_DENIED', 403)
        from zoneinfo import ZoneInfo
        start = datetime.combine(week, datetime.min.time(), ZoneInfo('Europe/Moscow'))
        rows = await self.repo.calendar_page(actor, start, start + timedelta(days=7), 100)
        return BookingsPage(items=[await self.booking_view(actor, row.id) for row in rows[:100]],
            next_cursor=rows[99].id if len(rows)>100 else None)

    async def linked_bookings(self, actor: int, connection: UUID, student_user_id: int,
                              cursor: UUID | None, limit: int) -> BookingsPage:
        if not 1 <= limit <= 100:
            raise IdentityError('INVALID_REQUEST', 422)
        await self.teacher(actor, connection)
        rows = await self.repo.linked_page(actor, connection, student_user_id, cursor, limit)
        return BookingsPage(items=[await self.booking_view(actor, row.id) for row in rows[:limit]],
            next_cursor=rows[limit-1].id if len(rows)>limit else None)


    async def capabilities(self, actor: int, enabled: bool) -> "PlanningCapabilities":
        from src.modules.integrations_vk.models_dto import PlanningCapabilities, PlanningConnection
        user = await self.user(actor, activated=True)
        if user.role != UserRole.TEACHER:
            raise IdentityError('SCOPE_DENIED', 403)
        rows = await self.repo.planning_connections(actor)
        return PlanningCapabilities(enabled=enabled,
            items=[PlanningConnection(connection_id=row.id, label='Запись · ' + row.group_id,
                                      enabled=row.enabled) for row in rows])

    async def close_windows(self, actor: int, data: "CloseWindowsRequest") -> OperationResult:
        await self.teacher(actor, data.connection_id)
        async def work() -> tuple[dict, dict]:
            await self.repo.schedules([actor])
            await self.teacher(actor, data.connection_id)
            revisions = {item.window_id: item.expected_revision for item in data.items}
            rows = await self.repo.rows(BookingWindow,
                BookingWindow.connection_id == data.connection_id,
                BookingWindow.teacher_user_id == actor, BookingWindow.id.in_(revisions), lock=True)
            if len(rows) != len(revisions):
                raise IdentityError('NOT_FOUND', 404)
            if any(row.revision != revisions[row.id] or row.status != 'published' for row in rows):
                raise IdentityError('STALE_REVISION')
            for row in rows:
                row.withdrawn, row.status = True, 'closed'
                row.revision += 1
            return {'kind': 'windows_closed', 'window_ids': [str(row.id) for row in rows]}, {}
        return (await self._operation(data.connection_id, 'windows_close', data.operation_id,
            data.model_dump(exclude={'operation_id'}), work, user_id=actor))[0]
