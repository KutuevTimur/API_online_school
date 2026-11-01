from src.modules.files.models_dto import FileDescriptorDTO
from src.modules.check_permission.models_dto import AccessContextDTO
from datetime import datetime
from enum import StrEnum
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


class HomeworkResponseDTO(ORMDTO, AccessContextDTO):
    course_id: int | None = None
    lesson_id: int | None = None
    student_user_id: int | None = None
    teacher_user_id: int | None = None
    course_name: str | None = None
    lesson_title: str | None = None
    file: FileDescriptorDTO | None = None
    working_submission_id: int | None = None
    can_submit: bool = False
    can_review: bool = False
    already_added: bool = False
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


class HomeworkListStatus(StrEnum):
    ALL = "all"
    TODO = "todo"
    SUBMITTED = "submitted"
    CHECKED = "checked"
