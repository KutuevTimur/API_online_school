from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class CreateHomeworkFixtureDTO(BaseModel):
    lesson_student_id: Optional[int] = None
    title: str = "Test Homework"
    description: Optional[str] = "Test Homework Description"
    original_file_path: Optional[str] = "/tmp/test.pdf"
    original_file_name: Optional[str] = "test.pdf"
    original_file_type: Optional[str] = "application/pdf"
    pdf_file_path: Optional[str] = "/tmp/test.pdf"
    pdf_file_name: Optional[str] = "test.pdf"
    deadline: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
