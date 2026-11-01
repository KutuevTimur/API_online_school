from src.modules.files.models_dto import FileDescriptorDTO
from src.modules.check_permission.models_dto import AccessContextDTO
from datetime import datetime
from pydantic import BaseModel
from src.modules.base.orm_dto import ORMDTO


class LectureDTO(ORMDTO):
    download_mime: str = "application/pdf"
    id: int
    lesson_student_id: int
    original_file_path: str
    original_file_name: str
    original_file_type: str
    pdf_file_path: str
    pdf_file_name: str
    created_at: datetime
    updated_at: datetime


class LectureResponseDTO(ORMDTO, AccessContextDTO):
    course_id: int | None = None
    lesson_id: int | None = None
    student_user_id: int | None = None
    teacher_user_id: int | None = None
    course_name: str | None = None
    lesson_title: str | None = None
    file: FileDescriptorDTO | None = None
    id: int
    original_file_name: str
    original_file_type: str
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

class CreateLectureFormRequestDTO(BaseModel):
    lesson_id: int
    student_user_id: int
