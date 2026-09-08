from datetime import datetime
from pydantic import BaseModel
from src.modules.base.orm_dto import ORMDTO


class LessonStudentDTO(ORMDTO):
    id: int
    lesson_id: int
    student_id: int
    created_at: datetime


class LessonStudentResponseDTO(ORMDTO):
    id: int
    lesson_id: int
    # Typically frontend uses student_user_id, but exposing student_id here until properties are requested.
    student_id: int
    created_at: datetime


class CreateLessonStudentRequestDTO(BaseModel):
    lesson_id: int
    # In requests from frontend, they likely send student_user_id, but the backend converts it.
    student_id: int
