from fastapi import APIRouter, Depends
from src.modules.check_permission.depends import get_current_admin_user
from src.modules.users.models_dto import UserDTO
from src.modules.teacher_students.depends import get_teacher_student_service
from src.modules.teacher_students.service import TeacherStudentService
from src.modules.teacher_students.models_dto import LinkTeacherStudentRequestDTO, TeacherStudentResponseDTO

router = APIRouter(prefix="/teacher_students", tags=["Teacher students"])


@router.post("", response_model=TeacherStudentResponseDTO, status_code=200)
async def link_teacher_student(
    data: LinkTeacherStudentRequestDTO,
    current_user: UserDTO = Depends(get_current_admin_user),
    service: TeacherStudentService = Depends(get_teacher_student_service),
) -> TeacherStudentResponseDTO:
    return await service.link(data, current_user.id)
