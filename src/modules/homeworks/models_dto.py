from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from src.modules.base.orm_dto import ORMDTO


class HomeworkDTO(ORMDTO):
    id: int
    lesson_student_id: int
    title: str
    description: Optional[str] = None
    original_file_path: Optional[str] = None
    original_file_name: Optional[str] = None
    original_file_type: Optional[str] = None
    pdf_file_path: Optional[str] = None
    pdf_file_name: Optional[str] = None
    deadline: datetime
    created_at: datetime
    updated_at: datetime


class HomeworkResponseDTO(ORMDTO):
    id: int
    title: str
    description: Optional[str] = None
    original_file_name: Optional[str] = None
    original_file_type: Optional[str] = None
    pdf_file_name: Optional[str] = None
    deadline: datetime
    created_at: datetime
    updated_at: datetime


class CreateHomeworkRequestDTO(BaseModel):
    lesson_student_id: int
    title: str
    description: Optional[str] = None
    original_file_path: Optional[str] = None
    original_file_name: Optional[str] = None
    original_file_type: Optional[str] = None
    pdf_file_path: Optional[str] = None
    pdf_file_name: Optional[str] = None
    deadline: datetime
