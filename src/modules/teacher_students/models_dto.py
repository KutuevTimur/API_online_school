from pydantic import BaseModel, Field


class LinkTeacherStudentRequestDTO(BaseModel):
    teacher_user_id: int = Field(gt=0)
    student_user_id: int = Field(gt=0)


class TeacherStudentResponseDTO(LinkTeacherStudentRequestDTO):
    active: bool
