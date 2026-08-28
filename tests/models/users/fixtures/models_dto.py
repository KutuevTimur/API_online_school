from typing import Optional

from pydantic import BaseModel

from src.models.users.models import UserRole


class CreateUserFixtureDTO(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    role: Optional[UserRole] = UserRole.TEACHER