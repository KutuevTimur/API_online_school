from typing import Optional
from pydantic import BaseModel

from src.modules.homework_submissions.models import HomeworkSubmissionStatus


class CreateHomeworkSubmissionFixtureDTO(BaseModel):
    homework_id: Optional[int] = None
    attempt_number: int = 1
    text_content: Optional[str] = "Submission text"
    status: Optional[HomeworkSubmissionStatus] = HomeworkSubmissionStatus.DRAFT
