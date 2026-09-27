from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from src.modules.base.orm_dto import ORMDTO
from src.modules.students.models_dto import StudentsResponseDTO


class CreateStudentCoursesDTO(BaseModel):
    student_id: int
    course_id: int

    is_deleted: Optional[bool] = False

    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class EnrollStudentRequestDTO(BaseModel):
    student_user_id: int


class StudentCourseResponseDTO(ORMDTO):
    id: int
    student_id: int
    course_id: int
    is_deleted: bool
    started_at: datetime
    expires_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    student: Optional[StudentsResponseDTO] = None
