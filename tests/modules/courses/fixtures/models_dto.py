from typing import Optional

from pydantic import BaseModel

from src.modules.courses.models import AvatarCoursesType


class CreateCourseFixtureDTO(BaseModel):
    teacher_id: Optional[int] = None
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    avatar_type: Optional[AvatarCoursesType] = AvatarCoursesType.DEFAULT
    avatar_path: Optional[str] = None
