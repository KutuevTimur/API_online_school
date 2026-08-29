from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from src.modules.base.orm_dto import ORMDTO


class TeachersDTO(ORMDTO):
    id: int
    user_id: int
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    avatar_url: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CreateTeacherDTO(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    avatar_url: Optional[str] = None
    description: Optional[str] = None


class UpdateTeacherDTO(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    avatar_url: Optional[str] = None
    description: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
