from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict
from src.modules.base.orm_dto import ORMDTO
from src.modules.students.models_dto import StudentsResponseDTO

class CreateStudentCoursesDTO(BaseModel):
    student_id: int
    course_id: int

    is_active: bool = True

    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class EnrollStudentRequestDTO(BaseModel):
    student_user_id: int


class StudentCourseResponseDTO(ORMDTO):
    id: int
    student_id: int
    course_id: int
    is_active: bool
    started_at: datetime
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    student: Optional[StudentsResponseDTO] = None
