from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from src.modules.base.orm_dto import ORMDTO


class StudentsDTO(ORMDTO):
    id: int
    user_id: int
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    avatar_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class StudentsResponseDTO(ORMDTO):
    user_id: int
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    avatar_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class CreateStudentDTO(BaseModel):
    user_id: int
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    avatar_path: Optional[str] = None


class UpdateStudentDTO(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    avatar_path: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
