from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CreateRefreshTokenFixtureDTO(BaseModel):
    user_id: Optional[int] = None
    token: Optional[str] = None
    is_revoked: Optional[bool] = False
    expires_at: Optional[datetime] = None