"""Public, action-specific read context. Never a substitute for write authorization."""
from typing import Literal
from pydantic import BaseModel


class AccessContextDTO(BaseModel):
    access_mode: Literal["active", "read_only"] = "read_only"
    read_only_reason: Literal["course_archived", "lesson_archived", "enrollment_ended",
        "access_expired", "teacher_link_ended", "history_only", "role_read_only"] | None = None
    can_manage: bool = False


class LessonRecipientResponseDTO(AccessContextDTO):
    school_grade: int | None = None
    student_user_id: int
    display_name: str
    username: str
