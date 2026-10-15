from src.modules.users.models_dto import UserAvatarResponseDTO
from src.modules.storage.download import private_download
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Response, Query, Request
from starlette import status
from fastapi.responses import FileResponse

from src.modules.auth.depends import get_current_user
from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.check_permission import get_current_teacher_user
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.courses.depends import get_courses_service
from src.modules.courses.models_dto import (
    CoursesResponseDTO,
    CreateCourseDTORequest,
    UpdateCourseDTORequest,
)
from src.modules.courses.service import CoursesService
from src.modules.users.models_dto import UserDTO

router = APIRouter(tags=["Course"])


@router.get(
    "/courses",
    response_model=PaginationResponseDTO[CoursesResponseDTO],
    status_code=status.HTTP_200_OK,
)
async def get_courses(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    teacher_user_id: Optional[int] = Query(None, description="Фильтр по создателю курса"),
    my_courses: Optional[bool] = Query(None, description="Поиск только своих курсов"),
    current_user: UserDTO = Depends(get_current_user),
    courses_service: CoursesService = Depends(get_courses_service),
):
    return await courses_service.list_visible(current_user, limit, offset, teacher_user_id)


@router.get(
    "/courses/{course_id}",
    response_model=CoursesResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def get_course_by_id(
    course_id: int,
    current_user: UserDTO = Depends(get_current_user),
    courses_service: CoursesService = Depends(get_courses_service),
):
    return await courses_service.detail_visible(current_user, course_id)


@router.post(
    "/courses",
    response_model=CoursesResponseDTO,
    status_code=status.HTTP_201_CREATED,
)
async def create_course(
    data: CreateCourseDTORequest,
    current_user: UserDTO = Depends(get_current_teacher_user),
    courses_service: CoursesService = Depends(get_courses_service),
):
    teacher = await courses_service.owner_profile(current_user)
    return await courses_service.create_course(teacher_id=teacher.id, data=data)


@router.patch(
    "/courses/{course_id}",
    response_model=CoursesResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def update_course(
    course_id: int,
    data: UpdateCourseDTORequest,
    current_user: UserDTO = Depends(get_current_teacher_user),
    courses_service: CoursesService = Depends(get_courses_service),
):
    teacher = await courses_service.owner_profile(current_user, course_id)
    return await courses_service.update_course(course_id=course_id, teacher_id=teacher.id, data=data)


@router.patch(
    "/courses/{course_id}/avatar",
    response_model=UserAvatarResponseDTO,
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
    teacher = await courses_service.owner_profile(current_user, course_id)
    await courses_service.update_avatar(course_id=course_id, teacher_id=teacher.id, avatar=avatar)
    return {"avatar_path": f"/courses/{course_id}/avatar"}


@router.delete(
    "/courses/{course_id}",
    response_model=CoursesResponseDTO,
    status_code=status.HTTP_200_OK,
)
async def delete_course(
    course_id: int,
    hard: bool = Query(False, description="Удалить безвозвратно"),
    current_user: UserDTO = Depends(get_current_teacher_user),
    courses_service: CoursesService = Depends(get_courses_service),
):
    await courses_service.detail_visible(current_user, course_id)
    teacher = await courses_service.owner_profile(current_user)
    if hard:
        raise PermissionErrorService("Purge is a separate admin workflow")
    else:
        return await courses_service.soft_delete_course(course_id=course_id, teacher_id=teacher.id)


@router.get("/courses/{course_id}/avatar", response_class=FileResponse, status_code=status.HTTP_200_OK)
async def get_course_avatar(
    request: Request,
    course_id: int,
    current_user: UserDTO = Depends(get_current_user),
    service: CoursesService = Depends(get_courses_service),
):
    return await private_download(request, str(await service.avatar_file(current_user, course_id)), "avatar.webp", "image/webp")
