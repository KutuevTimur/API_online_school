"""Local identity transaction owner. Transport admission belongs to F01.5.

observe_trusted is an internal port: only a verified adapter may call it. It is
not registered as an HTTP route. No bot imports, network I/O or live secrets.
"""
import hashlib
import json
import secrets
from datetime import UTC, datetime, timedelta
from typing import Awaitable, Callable
from uuid import UUID, uuid4
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.integrations_vk.exception import IdentityError
from src.modules.integrations_vk.models import (
    IntegrationConnection, ExternalContact, BookingRecipient, ExternalIdentityLink,
    ParentGrant, IdentityChallenge, IdentityOperation, VkActorContext,
)
from src.modules.integrations_vk.models_dto import (
    Candidate, ChallengeResponse, IdentityStatus, OperationResult, ResolveResponse,
)
from src.modules.integrations_vk.repository import IdentityRepository
from src.modules.integrations_vk.stages import (
    PrelockedWorkspace, stage_create_inactive_student, stage_link_student,
    stage_ensure_workspace, stage_bind_recipient, stage_materialize,
)
from src.modules.users.models import User, UserRole
from src.modules.students.models import Student
from src.modules.teachers.models import Teacher
from src.modules.audit_events.service import AuditEventsService


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class RetryDiscovery(Exception):
    """Prefix set changed: retry the whole transaction, never extend held locks."""


class IdentityService:
    def __init__(self, session: AsyncSession, users=None, clock: Callable = lambda: datetime.now(UTC)):
        self.session = session
        self.repo = IdentityRepository(session)
        self.users = users
        self.clock = clock

    async def connection(self, id: UUID) -> IntegrationConnection:
        connection = await self.repo.one(IntegrationConnection, IntegrationConnection.id == id)
        if connection is None:
            raise IdentityError('NOT_FOUND', 404)
        if not connection.enabled and not getattr(self, 'readonly', False):
            raise IdentityError('CONNECTION_DISABLED', 403)
        return connection

    async def user(self, id: int, *, lock: bool = False, activated: bool = False) -> User:
        user = await self.repo.one(User, User.id == id, lock=lock)
        if user is None or not user.is_active or (activated and not user.is_activated):
            raise IdentityError('ACCOUNT_BLOCKED')
        return user

    async def reauth(self, id: int, password: str) -> User:
        user = await self.user(id, activated=True)
        if not password or not self.users.verify_password(password, user.hashed_password):
            raise IdentityError('REAUTH_REQUIRED', 401)
        return user

    async def _operation(self, connection: UUID, action: str, operation: UUID, payload: dict,
                         work: Callable[[], Awaitable[tuple[dict, dict]]], *,
                         user_id: int | None = None, contact_id: UUID | None = None,
                         admit: Callable[[], Awaitable[None]] | None = None
                         ) -> tuple[OperationResult, dict]:
        owner = f'u:{user_id}' if user_id is not None else f'c:{connection}:{contact_id}'
        canonical = json.dumps({'connection': str(connection), 'action': action, **payload},
                               sort_keys=True, separators=(',', ':'), default=str)
        payload_hash = digest(canonical)
        for attempt in range(3):
            try:
                await self.connection(connection)
                if user_id is not None:
                    await self.user(user_id, activated=True)
                await self.repo.mutex(80420, f'{owner}:{action if user_id else ""}:{operation}')
                predicates = [IdentityOperation.owner_key == owner, IdentityOperation.operation_id == operation]
                if user_id is not None:
                    predicates.append(IdentityOperation.action == action)
                previous = await self.repo.one(IdentityOperation, *predicates)
                if previous is not None:
                    if previous.payload_hash != payload_hash:
                        raise IdentityError('PAYLOAD_MISMATCH')
                    if previous.state == 'rejected':
                        raise IdentityError(previous.error_code, 410 if previous.error_code in {'CHALLENGE_EXPIRED', 'HANDLE_EXPIRED'} else 409)
                    await self.session.commit()
                    return OperationResult(operation_id=operation, result=previous.result), {}
                if admit is not None:
                    await admit()
                    await self.session.flush()
                try:
                    async with self.session.begin_nested():
                        result, extra = await work()
                except IdentityError as exc:
                    if exc.status not in {409, 410}:
                        if admit is not None and exc.code == 'NOT_FOUND':
                            await self.session.commit()  # persist failed actor attempt only
                        raise
                    self.repo.stage(IdentityOperation, connection_id=connection, operation_id=operation,
                        owner_key=owner, actor_user_id=user_id, actor_contact_id=contact_id,
                        action=action, payload_hash=payload_hash, result=None,
                        state='rejected', error_code=exc.code)
                    await self.session.commit()
                    raise
                self.repo.stage(IdentityOperation, connection_id=connection, operation_id=operation,
                    owner_key=owner, actor_user_id=user_id, actor_contact_id=contact_id,
                    action=action, payload_hash=payload_hash, result=result)
                await self.session.commit()
                return OperationResult(operation_id=operation, result=result), extra
            except RetryDiscovery as exc:
                await self.session.rollback()
                if attempt == 2:
                    raise IdentityError('RETRY_LATER', 503) from exc
            except IntegrityError as exc:
                await self.session.rollback()
                raise IdentityError('IDENTITY_COLLISION') from exc
            except DBAPIError as exc:
                await self.session.rollback()
                code = getattr(exc.orig, 'sqlstate', None)
                if code not in {'40P01', '40001'}:
                    raise
                if attempt == 2:
                    raise IdentityError('RETRY_LATER', 503) from exc
            except Exception:
                await self.session.rollback()
                raise
        raise IdentityError('RETRY_LATER', 503)

    async def _contacts(self, connection: UUID, subjects: list[str]) -> dict[str, ExternalContact]:
        for subject in sorted(set(subjects)):
            await self.repo.mutex(80422, f'{connection}:community:{subject}')
        rows = await self.repo.rows(ExternalContact, ExternalContact.connection_id == connection,
                                    ExternalContact.subject.in_(subjects), lock=True)
        result = {row.subject: row for row in rows}
        for subject in sorted(set(subjects)):
            if subject not in result:
                result[subject] = self.repo.stage(ExternalContact, connection_id=connection, subject=subject)
        await self.session.flush()
        return result

    async def observe_trusted(self, connection_id: UUID, group_id: str, subject: str,
                              peer: str, teacher_user_id: int, candidate: Candidate,
                              child_subject: str | None = None) -> dict:
        """Internal verified message_new admission, synthetic adapter until F01.5.

        Parent's child_subject is a candidate only. A child must independently
        speak before teacher binding; grant approval never sets sender proof.
        """
        try:
            connection = await self.connection(connection_id)
            if group_id != connection.group_id or subject != peer or not subject.isdecimal() or int(subject) <= 0:
                raise IdentityError('SCOPE_DENIED', 403)
            if child_subject is not None and (not child_subject.isdecimal() or int(child_subject) <= 0 or child_subject == subject):
                raise IdentityError('INVALID_REQUEST', 422)
            if teacher_user_id not in await self.repo.teachers(connection_id):
                raise IdentityError('SCOPE_DENIED', 403)
            child_key = child_subject or subject
            contacts = await self._contacts(connection_id, [subject, child_key])
            actor, child = contacts[subject], contacts[child_key]
            actor.verified_sender_at = self.clock()
            recipient = await self.repo.one(BookingRecipient, BookingRecipient.connection_id == connection_id,
                                            BookingRecipient.child_contact_id == child.id, lock=True)
            if recipient is None:
                recipient = self.repo.stage(BookingRecipient, connection_id=connection_id,
                    child_contact_id=child.id, **candidate.model_dump())
                await self.session.flush()
            # Existing candidate/profile is immutable here, including parent guesses.
            await self.repo.add_recipient_teacher(connection_id, recipient.id, teacher_user_id)
            grant = None
            if child_subject:
                grant = await self.repo.one(ParentGrant, ParentGrant.connection_id == connection_id,
                    ParentGrant.parent_contact_id == actor.id, ParentGrant.recipient_id == recipient.id,
                    ParentGrant.teacher_user_id == teacher_user_id, lock=True)
                if grant is None:
                    grant = self.repo.stage(ParentGrant, connection_id=connection_id,
                        parent_contact_id=actor.id, recipient_id=recipient.id, teacher_user_id=teacher_user_id)
            raw = secrets.token_urlsafe(32)
            self.repo.stage(VkActorContext, connection_id=connection_id, contact_id=actor.id,
                contact_revision=actor.revision, digest=digest(raw), expires_at=self.clock() + timedelta(minutes=10))
            await self.session.commit()
            return {'actor_context': raw, 'recipient_id': str(recipient.id),
                    'grant_id': str(grant.id) if grant else None, 'grant_state': grant.state if grant else None}
        except Exception:
            await self.session.rollback()
            raise

    async def actor_context(self, raw: str) -> VkActorContext:
        context = await self.repo.one(VkActorContext, VkActorContext.digest == digest(raw))
        if context is None or context.expires_at <= self.clock():
            raise IdentityError('NOT_FOUND', 404)
        await self.connection(context.connection_id)
        contact = await self.repo.scoped(ExternalContact, context.connection_id, context.contact_id)
        if contact is None or contact.revision != context.contact_revision or contact.verified_sender_at is None:
            raise IdentityError('NOT_FOUND', 404)
        links = await self.repo.rows(ExternalIdentityLink, ExternalIdentityLink.contact_id == contact.id,
                                    ExternalIdentityLink.revoked_at.is_(None))
        for link in links:
            await self.user(link.user_id)
        return context

    async def issue_challenge(self, actor_id: int, session_key: str, password: str, data) -> ChallengeResponse:
        await self.reauth(actor_id, password)
        async def work():
            user = await self.user(actor_id, lock=True, activated=True)
            if not self.users.verify_password(password, user.hashed_password):
                raise IdentityError('REAUTH_REQUIRED', 401)
            if user.role.value != data.purpose:
                raise IdentityError('SCOPE_DENIED', 403)
            if data.purpose == 'teacher' and actor_id not in await self.repo.teachers(data.connection_id):
                raise IdentityError('SCOPE_DENIED', 403)
            # No retargeting while an active link exists. Unlink is explicit.
            active = await self.repo.one(ExternalIdentityLink, ExternalIdentityLink.connection_id == data.connection_id,
                ExternalIdentityLink.user_id == actor_id, ExternalIdentityLink.purpose == data.purpose,
                ExternalIdentityLink.revoked_at.is_(None))
            if active:
                raise IdentityError('IDENTITY_COLLISION')
            history = await self.repo.rows(ExternalIdentityLink, ExternalIdentityLink.connection_id == data.connection_id,
                ExternalIdentityLink.user_id == actor_id, ExternalIdentityLink.purpose == data.purpose)
            expected_revision = max((row.revision for row in history), default=0)
            # Bound concurrency: at most one unconsumed challenge per user/group/purpose.
            for previous in await self.repo.rows(IdentityChallenge, IdentityChallenge.connection_id == data.connection_id,
                    IdentityChallenge.user_id == actor_id, IdentityChallenge.purpose == data.purpose,
                    IdentityChallenge.consumed_at.is_(None), lock=True):
                previous.consumed_at = self.clock()
            raw = secrets.token_urlsafe(32)
            challenge = self.repo.stage(IdentityChallenge, connection_id=data.connection_id, user_id=actor_id,
                purpose=data.purpose, digest=digest(raw), session_digest=digest(session_key),
                auth_version=user.auth_version, expected_link_revision=expected_revision,
                expires_at=self.clock() + timedelta(minutes=10))
            await self.session.flush()
            return {'kind': 'challenge_issued', 'challenge_id': str(challenge.id)}, {'secret': raw}
        op, extra = await self._operation(data.connection_id, 'challenge_issue', data.operation_id,
            {'purpose': data.purpose, 'session': digest(session_key)}, work, user_id=actor_id)
        challenge = await self.repo.scoped(IdentityChallenge, data.connection_id, UUID(op.result['challenge_id']))
        return ChallengeResponse(operation=op, challenge_id=challenge.id,
                                 expires_at=challenge.expires_at, secret=extra.get('secret'))

    async def claim_challenge(self, data) -> OperationResult:
        context = await self.actor_context(data.actor_context)
        connection, contact_id = context.connection_id, context.contact_id
        async def admit():
            contact = await self.repo.scoped(ExternalContact, connection, contact_id, lock=True)
            await self.actor_context(data.actor_context)
            window = int(self.clock().timestamp()) // 600
            if contact.attempt_window == window and contact.attempts >= 5:
                raise IdentityError('RATE_LIMITED', 429)
            contact.attempts = contact.attempts + 1 if contact.attempt_window == window else 1
            contact.attempt_window = window

        async def work():
            challenge = await self.repo.one(IdentityChallenge, IdentityChallenge.connection_id == connection,
                                            IdentityChallenge.digest == digest(data.secret))
            if challenge is None:
                raise IdentityError('NOT_FOUND', 404)
            user = await self.user(challenge.user_id, lock=True, activated=True)
            challenge = await self.repo.scoped(IdentityChallenge, connection, challenge.id, lock=True)
            self._valid_challenge(challenge, user)
            if challenge.claimed_contact_id is not None:
                raise IdentityError('IDENTITY_COLLISION')
            link = await self.repo.one(ExternalIdentityLink, ExternalIdentityLink.contact_id == contact_id,
                ExternalIdentityLink.purpose == challenge.purpose, ExternalIdentityLink.revoked_at.is_(None))
            if link is not None:
                raise IdentityError('IDENTITY_COLLISION')
            contact = await self.repo.scoped(ExternalContact, connection, contact_id)
            contact.attempts -= 1
            challenge.claimed_contact_id = contact_id
            challenge.revision += 1
            return {'kind': 'identity_claimed', 'challenge_id': str(challenge.id)}, {}
        op, _ = await self._operation(connection, 'challenge_claim', data.operation_id,
            {'secret_digest': digest(data.secret)}, work, contact_id=contact_id, admit=admit)
        return op

    def _valid_challenge(self, challenge: IdentityChallenge, user: User) -> None:
        if user.role.value != challenge.purpose:
            raise IdentityError('SCOPE_DENIED', 403)
        if challenge.consumed_at is not None or challenge.auth_version != user.auth_version:
            raise IdentityError('NOT_FOUND', 404)
        if challenge.expires_at <= self.clock():
            raise IdentityError('CHALLENGE_EXPIRED', 410)

    async def confirm_challenge(self, actor_id: int, session_key: str, password: str,
                                 challenge_id: UUID, data) -> OperationResult:
        await self.reauth(actor_id, password)
        challenge = await self.repo.one(IdentityChallenge, IdentityChallenge.id == challenge_id,
                                        IdentityChallenge.user_id == actor_id)
        if challenge is None or challenge.session_digest != digest(session_key):
            raise IdentityError('NOT_FOUND', 404)
        connection, contact_id = challenge.connection_id, challenge.claimed_contact_id
        async def work():
            if contact_id is None:
                raise IdentityError('NOT_FOUND', 404)
            # All affected schedules, identity, workspace graph, Users, challenge.
            recipient = await self.repo.one(BookingRecipient, BookingRecipient.connection_id == connection,
                                            BookingRecipient.child_contact_id == contact_id)
            teachers = await self.repo.recipient_teachers(recipient.id) if recipient else []
            await self.repo.schedules(teachers)
            contact = await self.repo.scoped(ExternalContact, connection, contact_id, lock=True)
            recipient = await self.repo.scoped(BookingRecipient, connection, recipient.id, lock=True) if recipient else None
            if recipient and teachers != await self.repo.recipient_teachers(recipient.id):
                raise RetryDiscovery()
            links = await self.repo.rows(ExternalIdentityLink, ExternalIdentityLink.connection_id == connection,
                ExternalIdentityLink.contact_id == contact_id, ExternalIdentityLink.revoked_at.is_(None), lock=True)
            user = await self.user(actor_id, lock=True, activated=True)
            current = await self.repo.scoped(IdentityChallenge, connection, challenge_id, lock=True)
            self._valid_challenge(current, user)
            if current.revision != data.expected_revision:
                raise IdentityError('STALE_REVISION')
            if current.claimed_contact_id != contact_id or current.session_digest != digest(session_key):
                raise IdentityError('NOT_FOUND', 404)
            if any(link.purpose == current.purpose for link in links):
                raise IdentityError('IDENTITY_COLLISION')
            # User row lock serializes two challenges competing for one User.
            existing = await self.repo.one(ExternalIdentityLink, ExternalIdentityLink.connection_id == connection,
                ExternalIdentityLink.user_id == actor_id, ExternalIdentityLink.purpose == current.purpose,
                ExternalIdentityLink.revoked_at.is_(None))
            history = await self.repo.rows(ExternalIdentityLink, ExternalIdentityLink.connection_id == connection,
                ExternalIdentityLink.user_id == actor_id, ExternalIdentityLink.purpose == current.purpose)
            if max((row.revision for row in history), default=0) != current.expected_link_revision:
                raise IdentityError('STALE_REVISION')
            if existing or any(row.contact_id != contact_id for row in history):
                raise IdentityError('IDENTITY_COLLISION')
            if current.purpose == 'teacher' and actor_id not in await self.repo.teachers(connection):
                raise IdentityError('SCOPE_DENIED', 403)
            if current.purpose == 'student' and recipient:
                stage_bind_recipient(recipient, user)
            self.repo.stage(ExternalIdentityLink, connection_id=connection, contact_id=contact.id,
                user_id=actor_id, purpose=current.purpose, verified_method='self_challenge', verified_by=actor_id)
            current.consumed_at = self.clock()
            current.revision += 1
            AuditEventsService(self.session).stage(actor_id, 'vk_identity_link', 'user', actor_id)
            return {'kind': 'identity_linked', 'challenge_id': str(challenge_id)}, {}
        op, _ = await self._operation(connection, 'challenge_confirm', data.operation_id,
            {'challenge_id': str(challenge_id), 'revision': data.expected_revision, 'session': digest(session_key)},
            work, user_id=actor_id)
        return op

    async def status(self, actor_id: int, session_key: str) -> IdentityStatus:
        await self.user(actor_id, activated=True)
        links = await self.repo.rows(ExternalIdentityLink, ExternalIdentityLink.user_id == actor_id,
                                     ExternalIdentityLink.revoked_at.is_(None))
        challenges = await self.repo.rows(IdentityChallenge, IdentityChallenge.user_id == actor_id,
            IdentityChallenge.session_digest == digest(session_key), IdentityChallenge.consumed_at.is_(None),
            IdentityChallenge.expires_at > self.clock())
        pending = []
        for challenge in challenges:
            contact = await self.repo.scoped(ExternalContact, challenge.connection_id, challenge.claimed_contact_id) if challenge.claimed_contact_id else None
            pending.append({'challenge_id': str(challenge.id), 'revision': challenge.revision,
                'claimed_contact': '…' + contact.subject[-2:] if contact else None,
                'expires_at': challenge.expires_at.isoformat().replace('+00:00', 'Z')})
        connections = await self.repo.rows(IntegrationConnection, IntegrationConnection.enabled.is_(True))
        return IdentityStatus(connections=[{'connection_id': str(c.id), 'label': 'Запись · ' + c.group_id} for c in connections], items=[{'connection_id': str(link.connection_id), 'purpose': link.purpose,
            'revision': link.revision} for link in links], challenges=pending)

    async def unlink(self, actor_id: int, session_key: str, password: str, connection: UUID,
                      data) -> OperationResult:
        await self.reauth(actor_id, password)
        # Discovery only; rechecked under contact/recipient/link locks.
        found = await self.repo.one(ExternalIdentityLink, ExternalIdentityLink.connection_id == connection,
            ExternalIdentityLink.user_id == actor_id, ExternalIdentityLink.revoked_at.is_(None))
        found_id, contact_id = (found.id, found.contact_id) if found else (None, None)
        async def work():
            if found_id is None:
                raise IdentityError('NOT_FOUND', 404)
            contact = await self.repo.scoped(ExternalContact, connection, contact_id, lock=True)
            recipient = await self.repo.one(BookingRecipient, BookingRecipient.child_contact_id == contact.id, lock=True)
            link = await self.repo.scoped(ExternalIdentityLink, connection, found_id, lock=True)
            user = await self.user(actor_id, lock=True, activated=True)
            if not self.users.verify_password(password, user.hashed_password):
                raise IdentityError('REAUTH_REQUIRED', 401)
            if link.revoked_at or link.revision != data.expected_revision:
                raise IdentityError('STALE_REVISION')
            link.revoked_at = self.clock()
            link.revision += 1
            contact.revision += 1
            # Keep canonical User binding: unlink cannot permit a second account.
            if recipient:
                recipient.revision += 1
            AuditEventsService(self.session).stage(actor_id, 'vk_identity_unlink', 'user', actor_id)
            return {'kind': 'identity_unlinked'}, {}
        op, _ = await self._operation(connection, 'identity_unlink', data.operation_id,
            {'revision': data.expected_revision, 'session': digest(session_key)}, work, user_id=actor_id)
        return op

    async def decide_grant(self, actor_id: int, grant_id: UUID, decision: str, data) -> OperationResult:
        grant = await self.repo.one(ParentGrant, ParentGrant.id == grant_id, ParentGrant.teacher_user_id == actor_id)
        if grant is None:
            raise IdentityError('NOT_FOUND', 404)
        if decision not in {'confirm', 'reject', 'revoke'}:
            raise IdentityError('INVALID_REQUEST', 422)
        connection, parent_id, recipient_id = grant.connection_id, grant.parent_contact_id, grant.recipient_id
        if actor_id not in await self.repo.teachers(connection):
            raise IdentityError('SCOPE_DENIED', 403)
        async def work():
            await self.repo.scoped(ExternalContact, connection, parent_id, lock=True)
            await self.repo.scoped(BookingRecipient, connection, recipient_id, lock=True)
            current = await self.repo.scoped(ParentGrant, connection, grant_id, lock=True)
            actor = await self.user(actor_id, lock=True, activated=True)
            if actor.role != UserRole.TEACHER or actor_id not in await self.repo.teachers(connection):
                raise IdentityError('SCOPE_DENIED', 403)
            if current.revision != data.expected_revision:
                raise IdentityError('STALE_REVISION')
            if (decision in {'confirm', 'reject'} and current.state != 'pending') or (decision == 'revoke' and current.state != 'confirmed'):
                raise IdentityError('STALE_REVISION')
            current.state = {'confirm': 'confirmed', 'reject': 'rejected', 'revoke': 'revoked'}[decision]
            current.revision += 1
            current.approved_by, current.approved_at = actor_id, self.clock()
            current.proof_reference = data.operation_id
            AuditEventsService(self.session).stage(actor_id, 'vk_parent_' + decision, 'user', actor_id)
            return {'kind': 'grant_' + {'confirm':'confirmed', 'reject':'rejected', 'revoke':'revoked'}[decision],
                    'grant_id': str(grant_id)}, {}
        op, _ = await self._operation(connection, 'grant_' + decision, data.operation_id,
            {'grant': str(grant_id), 'revision': data.expected_revision}, work, user_id=actor_id)
        return op

    async def require_parent(self, raw: str, recipient_id: UUID, teacher_id: int) -> ParentGrant:
        context = await self.actor_context(raw)
        recipient = await self.repo.scoped(BookingRecipient, context.connection_id, recipient_id)
        if recipient is None:
            raise IdentityError('NOT_FOUND', 404)
        grant = await self.repo.one(ParentGrant, ParentGrant.connection_id == context.connection_id,
            ParentGrant.parent_contact_id == context.contact_id, ParentGrant.recipient_id == recipient_id,
            ParentGrant.teacher_user_id == teacher_id)
        if grant is None:
            raise IdentityError('NOT_FOUND', 404)
        if grant.state != 'confirmed':
            raise IdentityError('GRANT_PENDING' if grant.state == 'pending' else 'GRANT_REVOKED')
        if recipient.linked_student_user_id:
            await self.user(recipient.linked_student_user_id)
        return grant

    async def resolve_invite(self, actor_id: int, recipient_id: UUID, data, *, booking_id=None, booking_data=None) -> ResolveResponse:
        recipient = await self.repo.one(BookingRecipient, BookingRecipient.id == recipient_id)
        if recipient is None or actor_id not in await self.repo.recipient_teachers(recipient_id):
            raise IdentityError('NOT_FOUND', 404)
        connection, child_contact_id = recipient.connection_id, recipient.child_contact_id
        async def work():
            teachers = await self.repo.recipient_teachers(recipient_id)
            await self.repo.schedules(teachers)
            contact = await self.repo.scoped(ExternalContact, connection, child_contact_id, lock=True)
            current = await self.repo.scoped(BookingRecipient, connection, recipient_id, lock=True)
            if teachers != await self.repo.recipient_teachers(recipient_id):
                raise RetryDiscovery()
            links = await self.repo.rows(ExternalIdentityLink, ExternalIdentityLink.contact_id == contact.id,
                ExternalIdentityLink.purpose == 'student', ExternalIdentityLink.revoked_at.is_(None), lock=True)
            if current.revision != data.expected_revision:
                raise IdentityError('STALE_REVISION')
            if contact.verified_sender_at is None:
                raise IdentityError('SCOPE_DENIED', 403)
            actor = await self.repo.one(User, User.id == actor_id)
            if actor.role != UserRole.TEACHER or actor_id not in await self.repo.teachers(connection):
                raise IdentityError('SCOPE_DENIED', 403)
            if current.linked_student_user_id is not None:
                # A fresh operation must select the known account explicitly.
                if data.mode != 'own_student' or data.student_user_id != current.linked_student_user_id:
                    raise IdentityError('IDENTITY_COLLISION')
            if links and (data.mode != 'own_student' or links[0].user_id != data.student_user_id):
                raise IdentityError('IDENTITY_COLLISION')
            from src.modules.integrations_vk.models import Booking
            pending = await self.repo.rows(Booking, Booking.recipient_id == recipient_id,
                Booking.teacher_user_id == actor_id, Booking.status == 'confirmed', lock=True)
            if booking_id is not None:
                selected = next((b for b in pending if b.id == booking_id), None)
                if selected is None or selected.revision != booking_data.expected_revision:
                    raise IdentityError('STALE_REVISION')
            pending = [b for b in pending if b.lesson_id is None]
            if any(b.start_at <= self.clock() for b in pending) and not (booking_data and booking_data.review_past):
                raise IdentityError('REVIEW_REQUIRED')
            teacher = await self.repo.one(Teacher, Teacher.user_id == actor_id)
            student = await self.repo.one(Student, Student.user_id == data.student_user_id) if data.student_user_id else None
            if data.mode == 'own_student' and student is None:
                raise IdentityError('NOT_FOUND', 404)
            from src.modules.teacher_students.repository import TeacherStudentRepository
            from src.modules.courses.workspace_lock import lock_workspace_pair
            course = pair = None
            if student:
                await lock_workspace_pair(self.session, teacher.id, student.id)
                pair_repo = TeacherStudentRepository(self.session)
                course_ids = await pair_repo.lock_courses(teacher.id, student.id)
                pair = await pair_repo.previous_link(teacher.id, student.id)
                await pair_repo.memberships(teacher.id, student.id)
                candidates = await self.repo.workspace_candidates(teacher.id, student.id, eligible=True)
                if any(row.id not in course_ids for row in candidates):
                    raise RetryDiscovery()
                if len(candidates) > 1 or (not candidates and await self.repo.workspace_candidates(
                        teacher.id, student.id, eligible=False)):
                    raise IdentityError('COURSE_NOT_WRITABLE')
                course = candidates[0] if candidates else None
                if pair is None or pair.ended_at is not None:
                    raise IdentityError('ADMIN_LINK_REQUIRED')
            # Existing FK parents prelocked in ascending order before staged DML.
            user_ids = sorted({actor_id, *([student.user_id] if student else [])})
            locked = {id: await self.user(id, lock=True, activated=(id == actor_id)) for id in user_ids}
            target = locked.get(student.user_id) if student else None
            if target and target.is_activated:
                # Teacher may never substitute for the active User's self protocol.
                if not links or links[0].user_id != target.id:
                    raise IdentityError('SCOPE_DENIED', 403)
            if student:
                student = await self.repo.one(Student, Student.id == student.id, lock=True)
            else:
                target, student = await stage_create_inactive_student(self.session, self.users,
                    current.first_name, current.last_name, current.grade)
            context = PrelockedWorkspace(teacher.id, student.id, course, pair)
            await stage_link_student(self.session, context, student, allow_new=data.mode == 'new_student')
            workspace = await stage_ensure_workspace(self.session, context, student)
            stage_bind_recipient(current, target)
            if not links:
                self.repo.stage(ExternalIdentityLink, connection_id=connection, contact_id=contact.id,
                    user_id=target.id, purpose='student', verified_method='teacher_inactive', verified_by=actor_id)
            await stage_materialize(self.session, pending_bookings=pending, course_id=workspace.id,
                teacher_id=teacher.id, student_id=student.id)
            invitation = None
            if not target.is_activated:
                from src.modules.account_invitations.service import InvitationService
                from src.modules.users.models_dto import UserDTO
                invitation = await InvitationService(self.users).stage_issue(target, 'invite', UserDTO.model_validate(locked[actor_id]))
            AuditEventsService(self.session).stage(actor_id, 'vk_recipient_resolve', 'user', target.id)
            return {'kind': 'recipient_resolved', 'invitation_issued': invitation is not None}, {'invitation': invitation, 'student_username': target.username}
        op, extra = await self._operation(connection, 'recipient_resolve', data.operation_id,
            {'recipient': str(recipient_id), **data.model_dump(exclude={'operation_id'}),
             **({'booking': str(booking_id), 'booking_request': booking_data.model_dump(exclude={'operation_id'})} if booking_id else {})}, work, user_id=actor_id)
        return ResolveResponse(operation=op, invitation=extra.get('invitation'), student_username=extra.get('student_username'))

    async def operation_status(self, actor_id: int, operation_id: UUID, action: str) -> OperationResult:
        await self.user(actor_id, activated=True)
        row = await self.repo.one(IdentityOperation, IdentityOperation.actor_user_id == actor_id,
            IdentityOperation.operation_id == operation_id, IdentityOperation.action == action)
        if row is None:
            raise IdentityError('NOT_FOUND', 404)
        await self.connection(row.connection_id)
        return OperationResult(operation_id=operation_id, state=row.state, result=row.result,
            error={'code': row.error_code, 'retryable': False} if row.error_code else None)
