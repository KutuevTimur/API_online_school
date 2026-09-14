from fastapi import APIRouter, Depends
from starlette import status

from src.modules.check_permission import get_current_teacher_user
from src.modules.lesson_students.depends import get_lesson_students_service
from src.modules.lesson_students.models_dto import (
    AddStudentToLessonRequestDTO,
    CreateLessonStudentRequestDTO,
    LessonStudentResponseDTO
)
from src.modules.lesson_students.service import LessonStudentsService
from src.modules.users.models_dto import UserDTO

router = APIRouter(tags=["Lessons"])



@router.post(
    "/lessons/{lesson_id}/students",
    response_model=LessonStudentResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add a student to a lesson",
    description="Adds a student access to a specific lesson. Only the teacher who created the lesson can grant access."
)
async def add_student_to_lesson(
    lesson_id: int,
    data: AddStudentToLessonRequestDTO,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: LessonStudentsService = Depends(get_lesson_students_service),
):
    """
    Добавление ученика к занятию.
    Только для учителей, и только если урок принадлежит этому учителю.
    """
    create_dto = CreateLessonStudentRequestDTO(
        lesson_id=lesson_id,
        student_user_id=data.student_user_id
    )
    return await service.add_student(teacher_user_id=current_user.id, data=create_dto)


@router.delete(
    "/lessons/{lesson_id}/students/{student_user_id}",
    response_model=LessonStudentResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Remove a student from a lesson",
    description="Revokes a student's access to a specific lesson. Only the teacher who created the lesson can revoke access."
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
