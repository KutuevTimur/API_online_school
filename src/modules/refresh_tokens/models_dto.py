from datetime import datetime
from pydantic import BaseModel
from src.modules.base.orm_dto import ORMDTO


class RefreshTokenDTO(ORMDTO):
    refresh_token_id: int
    user_id: int
    digest: str
    family_id: str
    is_revoked: bool
    expires_at: datetime
    created_at: datetime


class CreateRefreshTokenDTO(BaseModel):
    user_id: int
    digest: str
    family_id: str
    expires_at: datetime
