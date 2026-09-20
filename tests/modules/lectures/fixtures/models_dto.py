from typing import Optional
from pydantic import BaseModel

class CreateLectureFixtureDTO(BaseModel):
    lesson_student_id: Optional[int] = None
    original_file_path: str = "/tmp/lecture.pdf"
    original_file_name: str = "lecture.pdf"
    original_file_type: str = "application/pdf"
    pdf_file_path: str = "/tmp/lecture.pdf"
    pdf_file_name: str = "lecture.pdf"
