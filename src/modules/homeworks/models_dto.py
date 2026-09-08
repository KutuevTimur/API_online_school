from datetime import datetime
from pydantic import BaseModel, ConfigDict
from src.modules.base.orm_dto import ORMDTO


class HomeworkDTO(ORMDTO):
    id: int
    lesson_student_id: int
    title: str
    description: str | None = None
    original_file_path: str | None = None
    original_file_name: str | None = None
    original_file_type: str | None = None
    pdf_file_path: str | None = None
    pdf_file_name: str | None = None
    deadline: datetime
    created_at: datetime
    updated_at: datetime


class HomeworkResponseDTO(ORMDTO):
    id: int
    lesson_student_id: int
    title: str
    description: str | None = None
    original_file_path: str | None = None
    original_file_name: str | None = None
    original_file_type: str | None = None
    pdf_file_path: str | None = None
    pdf_file_name: str | None = None
    deadline: datetime
    created_at: datetime
    updated_at: datetime


class CreateHomeworkRequestDTO(BaseModel):
    lesson_student_id: int
    title: str
    description: str | None = None
    original_file_path: str | None = None
    original_file_name: str | None = None
    original_file_type: str | None = None
    pdf_file_path: str | None = None
    pdf_file_name: str | None = None
    deadline: datetime


class UpdateHomeworkRequestDTO(BaseModel):
    title: str | None = None
    description: str | None = None
    original_file_path: str | None = None
    original_file_name: str | None = None
    original_file_type: str | None = None
    pdf_file_path: str | None = None
    pdf_file_name: str | None = None
    deadline: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
