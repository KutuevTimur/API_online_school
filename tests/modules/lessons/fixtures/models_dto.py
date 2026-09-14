from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

class CreateLessonFixtureDTO(BaseModel):
    course_id: Optional[int] = None
    teacher_id: Optional[int] = None
    
    title: str = "Test Lesson"
    topic: Optional[str] = "Test Topic"
    description: Optional[str] = "Test Description"
    
    scheduled_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    duration_minutes: Optional[int] = 60
