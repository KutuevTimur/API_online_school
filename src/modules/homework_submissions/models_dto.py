from src.modules.files.models_dto import FileDescriptorDTO
from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, ConfigDict, Field

from src.modules.base.orm_dto import ORMDTO
from src.modules.homework_submissions.models import HomeworkSubmissionStatus


class HomeworkSubmissionFileDTO(ORMDTO):
    download_mime: str = "application/pdf"
    id: int
    submission_id: int
    original_file_path: Optional[str] = None
    original_file_name: Optional[str] = None
    original_file_type: Optional[str] = None
    pdf_file_path: Optional[str] = None
    pdf_file_name: Optional[str] = None
    created_at: datetime


class HomeworkSubmissionFileResponseDTO(ORMDTO):
    file: FileDescriptorDTO | None = None
    id: int
    original_file_name: Optional[str] = None
    original_file_type: Optional[str] = None
    pdf_file_name: Optional[str] = None
    created_at: datetime


class HomeworkSubmissionDTO(ORMDTO):
    id: int
    homework_id: int
    attempt_number: int
    version: int = 1
    is_working: bool = True
    text_content: Optional[str] = None
    status: HomeworkSubmissionStatus
    grade: Optional[float] = None
    teacher_comment: Optional[str] = None
    submitted_at: Optional[datetime] = None
    checked_at: Optional[datetime] = None
    checked_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    files: List[HomeworkSubmissionFileDTO] = []


class HomeworkSubmissionResponseDTO(ORMDTO):
    """Данные ответа для клиента"""
    id: int
    homework_id: int
    attempt_number: int
    version: int = 1
    is_working: bool = True
    text_content: Optional[str] = None
    status: HomeworkSubmissionStatus
    grade: Optional[float] = None
    teacher_comment: Optional[str] = None
    submitted_at: Optional[datetime] = None
    checked_at: Optional[datetime] = None
    checked_by: Optional[int] = Field(None, description="user_id of the reviewing teacher")
    created_at: datetime
    updated_at: datetime
    
    files: List[HomeworkSubmissionFileResponseDTO] = []
    review_files: List[HomeworkSubmissionFileResponseDTO] = []


class HomeworkSubmissionRequestDTO(BaseModel):
    """Схема для инициализации записи (внутренняя)"""
    model_config = ConfigDict(from_attributes=True)
    homework_id: int
    attempt_number: int
    version: int = 1
    is_working: bool = True
    text_content: Optional[str] = None
    status: HomeworkSubmissionStatus = HomeworkSubmissionStatus.DRAFT
    grade: Optional[float] = None
    teacher_comment: Optional[str] = None
    submitted_at: Optional[datetime] = None
    checked_at: Optional[datetime] = None
    checked_by: Optional[int] = None


class HomeworkSubmissionFileRequestDTO(BaseModel):
    """Схема для создания записи файла (внутренняя)"""
    purpose: Literal["answer", "review"] = "answer"
    source_size: int | None = None
    original_asset_id: int | None = None
    download_asset_id: int | None = None
    submission_id: int
    original_file_path: str
    original_file_name: str
    original_file_type: str
    pdf_file_path: str
    pdf_file_name: str


class UpdateSubmissionStudentRequestDTO(BaseModel):
    """Обновление попытки учеником"""
    text_content: Optional[str] = None
    # Файлы передаются через UploadFile, поэтому здесь только текст


class UpdateSubmissionTeacherRequestDTO(BaseModel):
    """Final review of the exact answer version opened by the teacher."""
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(..., ge=1, strict=True)
    grade: int = Field(..., ge=0, le=5, strict=True)
    teacher_comment: Optional[str] = None
    status: Literal[HomeworkSubmissionStatus.CHECKED] = HomeworkSubmissionStatus.CHECKED


class ReviewQueueItemDTO(HomeworkSubmissionResponseDTO):
    course_id: int
    lesson_id: int
    student_user_id: int
    homework_title: str
    student_first_name: str
    student_last_name: str
    student_username: str
    course_name: str
