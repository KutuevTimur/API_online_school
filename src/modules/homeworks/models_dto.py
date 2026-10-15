from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from src.modules.base.orm_dto import ORMDTO


class HomeworkDTO(ORMDTO):
    download_mime: str = "application/pdf"
    id: int
    lesson_student_id: int
    title: str
    description: Optional[str] = None
    original_file_path: Optional[str] = None
    original_file_name: Optional[str] = None
    original_file_type: Optional[str] = None
    pdf_file_path: Optional[str] = None
    pdf_file_name: Optional[str] = None
    deadline: datetime | None = None
    created_at: datetime
    updated_at: datetime


class HomeworkResponseDTO(ORMDTO):
    submission_status: str | None = None
    placement_id: int | None = None
    placement_kind: str | None = None
    placement_lesson_id: int | None = None
    due_lesson_id: int | None = None
    deadline_frozen_at: datetime | None = None
    id: int
    title: str
    description: Optional[str] = None
    original_file_name: Optional[str] = None
    original_file_type: Optional[str] = None
    pdf_file_name: Optional[str] = None
    deadline: datetime | None = None
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
    deadline: datetime | None = None

class CreateHomeworkFormRequestDTO(BaseModel):
    lesson_id: int
    student_user_id: int
    title: str
    description: Optional[str] = None
