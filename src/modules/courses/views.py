from typing import List, Optional

from fastapi import APIRouter, Depends, UploadFile, File, Response, Query
from starlette import status

from src.modules.auth.depends import get_current_user
from src.modules.check_permission import get_current_teacher_user
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.courses.depends import get_courses_service
from src.modules.courses.exception import CourseNotFound
from src.modules.courses.models_dto import (
    CoursesDTO,
    CreateCourseDTORequest,
    UpdateCourseDTORequest,
)
from src.modules.courses.service import CoursesService
from src.modules.users.models import UserRole
from src.modules.users.models_dto import UserDTO

router = APIRouter(tags=["Course"])


@router.get(
    "/courses",
    response_model=List[CoursesDTO],
    status_code=status.HTTP_200_OK,
)
async def get_courses(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    is_active: Optional[bool] = Query(None),
    teacher_user_id: Optional[int] = Query(None, description="Фильтр курсов по преподавателю"),
    my_courses: Optional[bool] = Query(None, description="Только курсы текущего преподавателя"),
    current_user: UserDTO = Depends(get_current_user),
    courses_service: CoursesService = Depends(get_courses_service),
):
    if current_user.role == UserRole.TEACHER:
        teacher = None
        if teacher_user_id:
            teacher = await courses_service.teacher_repo.get_teacher_by_user_id(teacher_user_id)
            if not teacher:
                return []
        elif my_courses:
            teacher = await courses_service.teacher_repo.get_teacher_by_user_id(current_user.id)
            if not teacher:
                return []

        filter_teacher_id = teacher.id if teacher else None

        return await courses_service.get_all_courses(
            limit=limit,
            offset=offset,
            is_active=is_active,
            teacher_id=filter_teacher_id,
        )

    if current_user.role == UserRole.STUDENT:
        student = await courses_service.student_repo.get_student_by_user_id(current_user.id)
        if not student:
            return []

        return await courses_service.get_courses(
            student_id=student.id,
            is_active=True,
            limit=limit,
            offset=offset,
        )

    raise PermissionErrorService()


@router.get(
    "/courses/{course_id}",
    response_model=CoursesDTO,
    status_code=status.HTTP_200_OK,
)
async def get_course_by_id(
    course_id: int,
    current_user: UserDTO = Depends(get_current_user),
    courses_service: CoursesService = Depends(get_courses_service),
):
    course = await courses_service.get_course_by_id(course_id)
    if not course:
        raise CourseNotFound()

    if current_user.role == UserRole.TEACHER:
        return course

    if current_user.role == UserRole.STUDENT:
        if not course.is_active:
            raise PermissionErrorService()

        student = await courses_service.student_repo.get_student_by_user_id(current_user.id)
        if not student:
            raise PermissionErrorService()

        has_access = await courses_service.check_student_access(
            student_id=student.id,
            course_id=course_id,
        )
        if not has_access:
            raise PermissionErrorService()

        return course

    raise PermissionErrorService()


@router.post(
    "/courses",
    response_model=CoursesDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_course(
    data: CreateCourseDTORequest,
    current_user: UserDTO = Depends(get_current_teacher_user),
    courses_service: CoursesService = Depends(get_courses_service),
):
    teacher = await courses_service.teacher_repo.get_teacher_by_user_id(current_user.id)
    return await courses_service.create_course(teacher_id=teacher.id, data=data)


@router.patch(
    "/courses/{course_id}",
    response_model=CoursesDTO,
    status_code=status.HTTP_200_OK,
)
async def update_course(
    course_id: int,
    data: UpdateCourseDTORequest,
    current_user: UserDTO = Depends(get_current_teacher_user),
    courses_service: CoursesService = Depends(get_courses_service),
):
    teacher = await courses_service.teacher_repo.get_teacher_by_user_id(current_user.id)
    return await courses_service.update_course(course_id=course_id, teacher_id=teacher.id, data=data)


@router.patch(
    "/courses/{course_id}/avatar",
    status_code=status.HTTP_200_OK,
)
@router.patch(
    "/course_avatare/{course_id}",
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
async def update_avatar(
    course_id: int,
    avatar: UploadFile = File(...),
    current_user: UserDTO = Depends(get_current_teacher_user),
    courses_service: CoursesService = Depends(get_courses_service),
):
    file_bytes = await avatar.read()
    await avatar.seek(0)
    teacher = await courses_service.teacher_repo.get_teacher_by_user_id(current_user.id)
    await courses_service.update_avatar(course_id=course_id, teacher_id=teacher.id, avatar=avatar)

    return Response(
        content=file_bytes,
        media_type=avatar.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'inline; filename="{avatar.filename}"'
        },
    )


@router.delete(
    "/courses/{course_id}",
    response_model=CoursesDTO,
    status_code=status.HTTP_200_OK,
)
async def delete_course(
    course_id: int,
    hard: bool = Query(False, description="Физическое удаление вместо мягкого"),
    current_user: UserDTO = Depends(get_current_teacher_user),
    courses_service: CoursesService = Depends(get_courses_service),
):
    teacher = await courses_service.teacher_repo.get_teacher_by_user_id(current_user.id)
    if hard:
        return await courses_service.delete_course(course_id=course_id, teacher_id=teacher.id)
    return await courses_service.soft_delete_course(course_id=course_id, teacher_id=teacher.id)
