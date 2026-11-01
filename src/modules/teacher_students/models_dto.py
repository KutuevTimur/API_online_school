from datetime import datetime
from pydantic import BaseModel, Field
from src.modules.users.models_dto import MinimalProfileResponseDTO


class LinkTeacherStudentRequestDTO(BaseModel):
    teacher_user_id: int = Field(gt=0)
    student_user_id: int = Field(gt=0)


class TeacherStudentResponseDTO(LinkTeacherStudentRequestDTO):
    active: bool


class AdminTeacherStudentResponseDTO(TeacherStudentResponseDTO):
    teacher: MinimalProfileResponseDTO
    student: MinimalProfileResponseDTO
    ended_at: datetime | None
