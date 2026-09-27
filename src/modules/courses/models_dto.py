from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from src.modules.base.orm_dto import ORMDTO
from src.modules.courses.models import AvatarCoursesType


class CoursesDTO(ORMDTO):
    id: int
    teacher_id: int
    teacher_user_id: int
    name: str
    slug: str
    description: Optional[str] = None
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
    avatar_type: AvatarCoursesType
    avatar_path: Optional[str] = None

    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None


class CreateCourseDTO(BaseModel):
    teacher_id: int
    name: str
    slug: str
    description: Optional[str] = None
    avatar_type: AvatarCoursesType = AvatarCoursesType.DEFAULT
    avatar_path: Optional[str] = None



class CreateCourseDTORequest(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None



class UpdateCourseDTO(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    avatar_type: Optional[AvatarCoursesType] = None
    avatar_path: Optional[str] = None
    is_deleted: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class UpdateCourseDTORequest(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    avatar_type: Optional[AvatarCoursesType] = None
    is_deleted: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)
