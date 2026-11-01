from datetime import datetime
from typing import Optional

from pydantic import field_serializer, BaseModel, ConfigDict, Field

from src.modules.base.orm_dto import ORMDTO


class StudentsDTO(ORMDTO):
    id: int
    user_id: int
    school_grade: int | None = Field(default=None, ge=1, le=11)
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    avatar_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class StudentsResponseDTO(ORMDTO):
    user_id: int
    school_grade: int | None = Field(default=None, ge=1, le=11)
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    avatar_path: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    @field_serializer("avatar_path")
    def serialize_avatar(self, value: str | None) -> str | None:
        return f"/users/{self.user_id}/avatar" if value else None


class CreateStudentDTO(BaseModel):
    user_id: int
    school_grade: int | None = Field(default=None, ge=1, le=11)
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


class MinimalStudentResponseDTO(ORMDTO):
    user_id: int
    school_grade: int | None = Field(default=None, ge=1, le=11)
    first_name: str
    last_name: str
    avatar_path: str | None = None

    @field_serializer("avatar_path")
    def serialize_avatar(self, value: str | None) -> str | None:
        return f"/users/{self.user_id}/avatar" if value else None
