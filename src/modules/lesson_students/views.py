from fastapi import APIRouter, Depends
from starlette import status

from src.modules.check_permission import get_current_teacher_user
from src.modules.lesson_students.depends import get_lesson_students_service
from src.modules.lesson_students.models_dto import CreateLessonStudentRequestDTO, LessonStudentResponseDTO
from src.modules.lesson_students.service import LessonStudentsService
from src.modules.users.models_dto import UserDTO

router = APIRouter(tags=["Lesson Students"])


@router.post(
    "/lesson-students",
    response_model=LessonStudentResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def add_student_to_lesson(
    data: CreateLessonStudentRequestDTO,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: LessonStudentsService = Depends(get_lesson_students_service),
):
    """
    Добавление ученика к занятию.
    Только для учителей, и только если урок принадлежит этому учителю.
    """
    return await service.add_student(teacher_user_id=current_user.id, data=data)


@router.delete(
    "/lesson-students/{lesson_id}/{student_user_id}",
    response_model=LessonStudentResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def remove_student_from_lesson(
    lesson_id: int,
    student_user_id: int,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: LessonStudentsService = Depends(get_lesson_students_service),
):
    """
    Удаление ученика с занятия.
    Только для учителей, и только если урок принадлежит этому учителю.
    """
    return await service.remove_student(
        teacher_user_id=current_user.id,
        lesson_id=lesson_id,
        student_user_id=student_user_id,
    )
