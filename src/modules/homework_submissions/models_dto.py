from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from src.modules.base.orm_dto import ORMDTO
from src.modules.homework_submissions.models import HomeworkSubmissionStatus


class HomeworkSubmissionFileDTO(ORMDTO):
    id: int
    submission_id: int
    original_file_path: Optional[str] = None
    original_file_name: Optional[str] = None
    original_file_type: Optional[str] = None
    pdf_file_path: Optional[str] = None
    pdf_file_name: Optional[str] = None
    created_at: datetime


class HomeworkSubmissionFileResponseDTO(ORMDTO):
    id: int
    original_file_name: Optional[str] = None
    original_file_type: Optional[str] = None
    pdf_file_name: Optional[str] = None
    created_at: datetime


class HomeworkSubmissionDTO(ORMDTO):
    id: int
    homework_id: int
    attempt_number: int
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
    text_content: Optional[str] = None
    status: HomeworkSubmissionStatus
    grade: Optional[float] = None
    teacher_comment: Optional[str] = None
    submitted_at: Optional[datetime] = None
    checked_at: Optional[datetime] = None
    checked_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    files: List[HomeworkSubmissionFileResponseDTO] = []


class HomeworkSubmissionRequestDTO(BaseModel):
    """Схема для инициализации записи (внутренняя)"""
    model_config = ConfigDict(from_attributes=True)
    homework_id: int
    attempt_number: int
    text_content: Optional[str] = None
    status: HomeworkSubmissionStatus = HomeworkSubmissionStatus.DRAFT
    grade: Optional[float] = None
    teacher_comment: Optional[str] = None
    submitted_at: Optional[datetime] = None
    checked_at: Optional[datetime] = None
    checked_by: Optional[int] = None


class HomeworkSubmissionFileRequestDTO(BaseModel):
    """Схема для создания записи файла (внутренняя)"""
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
    """Обновление попытки учителем"""
    status: Optional[HomeworkSubmissionStatus] = None
    grade: Optional[float] = None
    teacher_comment: Optional[str] = None


class UpdateSubmissionTeacherDTO(UpdateSubmissionTeacherRequestDTO):
    """Обновление попытки учителем. Используется для передачи в repository layer"""
    checked_at: Optional[datetime] = None
    checked_by: Optional[int] = None
    updated_at: Optional[datetime] = None

    @staticmethod
    def from_request_dto(obj: UpdateSubmissionTeacherRequestDTO) -> 'UpdateSubmissionTeacherDTO':
        return UpdateSubmissionTeacherDTO(
            **obj.model_dump(exclude_unset=True),
        )
