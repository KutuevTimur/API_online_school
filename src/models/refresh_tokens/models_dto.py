from datetime import datetime

from pydantic import BaseModel

from src.models.base.orm_dto import ORMDTO


class RefreshTokenDTO(ORMDTO):
    refresh_token_id: int
    user_id: int
    token: str
    is_revoked: bool
    expires_at: datetime
    created_at: datetime


class CreateRefreshTokenDTO(BaseModel):
    user_id: int
    token: str
    expires_at: datetime