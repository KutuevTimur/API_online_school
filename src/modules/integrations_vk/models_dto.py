from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator
from src.modules.account_invitations.models_dto import InvitationResponse

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Positive = Annotated[int, Field(gt=0, strict=True)]


class StrictDTO(BaseModel):
    model_config = ConfigDict(extra='forbid')


class Candidate(StrictDTO):
    first_name: Name
    last_name: Name
    grade: Annotated[int, Field(ge=1, le=11, strict=True)] | None = None


class OperationRequest(StrictDTO):
    operation_id: UUID


class RevisionRequest(OperationRequest):
    expected_revision: Positive


class IssueChallengeRequest(OperationRequest):
    connection_id: UUID
    purpose: Literal['student', 'teacher']


class ClaimChallengeRequest(OperationRequest):
    actor_context: Annotated[str, Field(min_length=32, max_length=128)]
    secret: Annotated[str, Field(min_length=32, max_length=128)]


class ResolveRecipientRequest(RevisionRequest):
    mode: Literal['new_student', 'own_student']
    student_user_id: Positive | None = None

    @model_validator(mode='after')
    def mode_target(self):
        if (self.mode == 'own_student') != (self.student_user_id is not None):
            raise ValueError('mode/target mismatch')
        return self


class OperationResult(StrictDTO):
    operation_id: UUID
    state: Literal['committed', 'rejected'] = 'committed'
    result: dict | None
    error: dict | None = None
    current: dict | None = None
    delivery: dict = Field(default_factory=lambda: {'state': 'not_planned'})


class ChallengeResponse(StrictDTO):
    operation: OperationResult
    challenge_id: UUID
    secret: str | None = None
    expires_at: datetime


class ResolveResponse(StrictDTO):
    operation: OperationResult
    invitation: InvitationResponse | None = None
    student_username: str | None = None


class IdentityStatus(StrictDTO):
    items: list[dict]
    challenges: list[dict]
    connections: list[dict] = Field(default_factory=list)


from datetime import date, UTC, timedelta
from zoneinfo import ZoneInfo
from pydantic import AwareDatetime


class WindowItem(StrictDTO):
    start_at: AwareDatetime
    end_at: AwareDatetime

    @model_validator(mode='after')
    def interval(self):
        self.start_at, self.end_at = self.start_at.astimezone(UTC), self.end_at.astimezone(UTC)
        seconds = (self.end_at - self.start_at).total_seconds()
        if seconds <= 0 or seconds % 60 or seconds > 1440 * 60:
            raise ValueError('Expected a positive whole-minute interval up to one day')
        return self


class PublishWindowsRequest(OperationRequest):
    connection_id: UUID
    week_start: date
    items: Annotated[list[WindowItem], Field(min_length=1, max_length=100)]

    @model_validator(mode='after')
    def dated_week(self):
        if self.week_start.weekday() != 0:
            raise ValueError('Expected a dated Moscow Monday')
        for item in self.items:
            start, end = item.start_at.astimezone(ZoneInfo('Europe/Moscow')), item.end_at.astimezone(ZoneInfo('Europe/Moscow'))
            if start.date() < self.week_start or end.date() > self.week_start + timedelta(days=7) or (end.date() == self.week_start + timedelta(days=7) and end.time().isoformat() != '00:00:00'):
                raise ValueError('Window outside selected Moscow week')
        return self


class PrepareBookingRequest(StrictDTO):
    actor_context: Annotated[str, Field(min_length=32, max_length=128)]
    recipient_id: UUID
    window_id: UUID
    expected_revision: Positive


class ConfirmBookingRequest(RevisionRequest):
    actor_context: Annotated[str, Field(min_length=32, max_length=128)]
    handle: Annotated[str, Field(min_length=32, max_length=128)]


class MaterializeRequest(RevisionRequest):
    expected_recipient_revision: Positive
    review_past: bool = Field(default=False, strict=True)


class BookingResolveRequest(MaterializeRequest):
    mode: Literal['new_student', 'own_student']
    student_user_id: Positive | None = None

    @model_validator(mode='after')
    def target(self):
        if (self.mode == 'own_student') != (self.student_user_id is not None):
            raise ValueError('mode/target mismatch')
        return self


class WindowView(StrictDTO):
    window_id: UUID
    revision: int
    start_at: datetime
    end_at: datetime
    status: str


class ParentGrantView(StrictDTO):
    grant_id: UUID
    revision: int
    state: Literal['pending', 'confirmed', 'rejected', 'revoked']
    parent_label: str


class RecipientView(StrictDTO):
    recipient_id: UUID
    revision: int
    first_name: str
    last_name: str
    grade: int | None
    linked_student_user_id: int | None
    parent_grants: list[ParentGrantView]


class BookingView(StrictDTO):
    booking_id: UUID
    revision: int
    start_at: datetime
    end_at: datetime
    status: Literal['confirmed', 'cancelled']
    recipient: RecipientView
    lesson_id: int | None
    access_state: str
    lesson_price_kopecks: int | None
    delivery_state: str = 'not_planned'


class PreparedBookingResponse(StrictDTO):
    handle: str
    operation_id: UUID
    expires_at: datetime


class WindowsPage(StrictDTO):
    items: list[WindowView]
    next_cursor: UUID | None = None


class BookingsPage(StrictDTO):
    items: list[BookingView]
    next_cursor: UUID | None = None


class PlanningConnection(StrictDTO):
    connection_id: UUID
    label: str
    enabled: bool


class PlanningCapabilities(StrictDTO):
    enabled: bool
    items: list[PlanningConnection]
