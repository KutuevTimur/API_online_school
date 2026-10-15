from src.modules.auth.password_dto import Password
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
from src.modules.users.models_dto import UserResponse


class InvitationResponse(BaseModel):
    activation_link: str | None = None
    expires_at: datetime | None = None


class InvitationUserResponse(UserResponse, InvitationResponse):
    pass


class IssueInvitationRequest(BaseModel):
    user_id: int = Field(gt=0)
    purpose: Literal["invite", "reset"]


class ConsumeInvitationRequest(BaseModel):
    token: str = Field(min_length=1, max_length=256)
    purpose: Literal["invite", "reset"]
    new_password: Password


class ConsumeInvitationResponse(BaseModel):
    success: bool
