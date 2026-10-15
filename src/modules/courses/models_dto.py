from datetime import datetime
from typing import Optional

from pydantic import field_serializer, BaseModel, ConfigDict

from src.modules.base.orm_dto import ORMDTO
from src.modules.base.url_validation import CallURL
from src.modules.courses.models import AvatarCoursesType


class CoursesDTO(ORMDTO):
    id: int
    teacher_id: int
    teacher_user_id: int
    name: str
    slug: str
    description: Optional[str] = None
    call_url: CallURL | None = None
    avatar_type: AvatarCoursesType
    avatar_path: Optional[str] = None

    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class CoursesResponseDTO(ORMDTO):
    id: int
    teacher_user_id: int
    name: str
    slug: str
    description: Optional[str] = None
    call_url: CallURL | None = None
    avatar_type: AvatarCoursesType
    avatar_path: Optional[str] = None

    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    @field_serializer("avatar_path")
    def serialize_avatar(self, value: str | None) -> str | None:
        return f"/courses/{self.id}/avatar" if value else None


class CreateCourseDTO(BaseModel):
    teacher_id: int
    name: str
    slug: str
    description: Optional[str] = None
    call_url: CallURL | None = None
    avatar_type: AvatarCoursesType = AvatarCoursesType.DEFAULT
    avatar_path: Optional[str] = None



class CreateCourseDTORequest(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    call_url: CallURL | None = None



class UpdateCourseDTO(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    call_url: CallURL | None = None
    avatar_type: Optional[AvatarCoursesType] = None
    avatar_path: Optional[str] = None
    is_deleted: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class UpdateCourseDTORequest(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    call_url: CallURL | None = None
    avatar_type: Optional[AvatarCoursesType] = None
    is_deleted: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)
