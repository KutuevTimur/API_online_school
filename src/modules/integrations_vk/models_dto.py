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
    current: None = None
    delivery: dict = Field(default_factory=lambda: {'state': 'not_planned'})


class ChallengeResponse(StrictDTO):
    operation: OperationResult
    challenge_id: UUID
    secret: str | None = None
    expires_at: datetime


class ResolveResponse(StrictDTO):
    operation: OperationResult
    invitation: InvitationResponse | None = None


class IdentityStatus(StrictDTO):
    items: list[dict]
    challenges: list[dict]
