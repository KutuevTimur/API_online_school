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
    student_user_id: int
    created_at: datetime


class CreateLessonStudentRequestDTO(BaseModel):
    lesson_id: int
    student_user_id: int


class CreateLessonStudentDTO(BaseModel):
    lesson_id: int
    student_id: int


class AddStudentToLessonRequestDTO(BaseModel):
    student_user_id: int
