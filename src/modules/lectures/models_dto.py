from datetime import datetime
from pydantic import BaseModel, ConfigDict
from src.modules.base.orm_dto import ORMDTO


class LectureDTO(ORMDTO):
    id: int
    lesson_student_id: int
    original_file_path: str
    original_file_name: str
    original_file_type: str
    pdf_file_path: str
    pdf_file_name: str
    created_at: datetime
    updated_at: datetime


class LectureResponseDTO(ORMDTO):
    id: int
    lesson_student_id: int
    original_file_path: str
    original_file_name: str
    original_file_type: str
    pdf_file_path: str
    pdf_file_name: str
    created_at: datetime
    updated_at: datetime


class CreateLectureRequestDTO(BaseModel):
    lesson_student_id: int
    original_file_path: str
    original_file_name: str
    original_file_type: str
    pdf_file_path: str
    pdf_file_name: str


class UpdateLectureRequestDTO(BaseModel):
    original_file_path: str | None = None
    original_file_name: str | None = None
    original_file_type: str | None = None
    pdf_file_path: str | None = None
    pdf_file_name: str | None = None

    model_config = ConfigDict(from_attributes=True)
