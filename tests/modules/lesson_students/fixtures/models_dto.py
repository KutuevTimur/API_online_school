from typing import Optional
from pydantic import BaseModel

class CreateLessonStudentFixtureDTO(BaseModel):
    lesson_id: Optional[int] = None
    student_id: Optional[int] = None
