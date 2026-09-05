from typing import Optional

from pydantic import BaseModel


class CreateTeacherCoursesDTO(BaseModel):
    teacher_id: int
    course_id: int
    is_active: Optional[bool] = True
