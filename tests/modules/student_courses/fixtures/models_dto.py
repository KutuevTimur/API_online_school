from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class CreateStudentCourseFixtureDTO(BaseModel):
    student_id: Optional[int] = None
    course_id: Optional[int] = None
    is_active: bool = True
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
