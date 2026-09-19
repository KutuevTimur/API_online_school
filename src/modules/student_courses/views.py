from fastapi import APIRouter, Depends, Query
from starlette import status

from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.auth.depends import get_current_user
from src.modules.check_permission.depends import get_current_teacher_user
from src.modules.users.models_dto import UserDTO

from src.modules.student_courses.depends import get_student_courses_service
from src.modules.student_courses.models_dto import (
    EnrollStudentRequestDTO,
    StudentCourseResponseDTO
)
from src.modules.student_courses.service import StudentCoursesService

router = APIRouter(tags=["Student Courses"])

@router.post(
    "/courses/{course_id}/students",
    response_model=StudentCourseResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Зачислить ученика на курс",
)
async def enroll_student_to_course(
    course_id: int,
    data: EnrollStudentRequestDTO,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: StudentCoursesService = Depends(get_student_courses_service),
):
    return await service.enroll_student(
        teacher_user_id=current_user.id,
        course_id=course_id,
        data=data,
    )


@router.delete(
    "/courses/{course_id}/students/{student_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Отчислить ученика",
)
async def unenroll_student_from_course(
    course_id: int,
    student_user_id: int,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: StudentCoursesService = Depends(get_student_courses_service),
):
    await service.unenroll_student(
        teacher_user_id=current_user.id,
        course_id=course_id,
        student_user_id=student_user_id,
    )


@router.get(
    "/courses/{course_id}/students",
    response_model=PaginationResponseDTO[StudentCourseResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Получить список всех учеников, прикрепленных к курсу",
)
async def get_students_for_course(
    course_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: StudentCoursesService = Depends(get_student_courses_service),
):
    total, students = await service.get_students_for_course(
        teacher_user_id=current_user.id,
        course_id=course_id,
        limit=limit,
        offset=offset,
    )
    return PaginationResponseDTO[StudentCourseResponseDTO](
        total=total,
        limit=limit,
        offset=offset,
        items=students,
    )
