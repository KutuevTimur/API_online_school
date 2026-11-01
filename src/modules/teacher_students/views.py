from fastapi import APIRouter, Depends, Path, Query, Response
from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.teacher_students.models_dto import AdminTeacherStudentResponseDTO
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


@router.get("", response_model=PaginationResponseDTO[AdminTeacherStudentResponseDTO], status_code=200)
async def list_links(
    teacher_user_id: int | None = Query(None, gt=0),
    student_user_id: int | None = Query(None, gt=0),
    active: bool | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=2147483647),
    actor: UserDTO = Depends(get_current_admin_user),
    service: TeacherStudentService = Depends(get_teacher_student_service),
) -> PaginationResponseDTO[AdminTeacherStudentResponseDTO]:
    items, total = await service.page(actor.id, teacher_user_id, student_user_id, active, limit, offset)
    return PaginationResponseDTO(items=items, total=total, limit=limit, offset=offset)


@router.delete("/{teacher_user_id}/{student_user_id}", status_code=204, response_class=Response)
async def end_link(
    teacher_user_id: int = Path(gt=0),
    student_user_id: int = Path(gt=0),
    actor: UserDTO = Depends(get_current_admin_user),
    service: TeacherStudentService = Depends(get_teacher_student_service),
) -> Response:
    await service.end(LinkTeacherStudentRequestDTO(teacher_user_id=teacher_user_id,
        student_user_id=student_user_id), actor.id)
    return Response(status_code=204)
