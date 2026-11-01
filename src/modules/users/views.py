from typing import Literal
from src.modules.storage.download import private_download
from fastapi import APIRouter, Depends, UploadFile, File, Response, Query, Request
from starlette import status
from fastapi.responses import FileResponse

from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.auth.depends import get_current_user
from src.modules.check_permission import get_current_user_with_target_permission
from src.modules.students.models_dto import StudentsResponseDTO
from src.modules.teachers.models_dto import TeachersResponseDTO
from src.modules.users.depends import get_user_service
from src.modules.users.models_dto import UserAvatarResponseDTO, MinimalProfileResponseDTO, AdminAccountStatusRequestDTO, UserResponse, UserDTO, UpdateUserDataRequestDTO, PublicProfileResponseDTO
from src.modules.users.service import UsersService

from src.modules.users.models_dto import StudentSort, TeacherStudentProfileResponseDTO

router = APIRouter(prefix="/users",  tags=["User"])


@router.get("/students", response_model=PaginationResponseDTO[PublicProfileResponseDTO | TeacherStudentProfileResponseDTO | MinimalProfileResponseDTO], status_code=status.HTTP_200_OK)
async def get_students(
    sort: StudentSort = Query(StudentSort.RECENT),
    attention: Literal["homework", "lecture"] | None = Query(None),
    school_grade: int | None = Query(None, ge=1, le=11),
    q: str | None = Query(None, min_length=1, max_length=100),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: UserDTO = Depends(get_current_user),
    user_service: UsersService = Depends(get_user_service),
):
    total, items = await user_service.get_students(actor=current_user, limit=limit, offset=offset, q=q, school_grade=school_grade, sort=sort, attention=attention)
    return PaginationResponseDTO[PublicProfileResponseDTO | TeacherStudentProfileResponseDTO | MinimalProfileResponseDTO](
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/teachers", response_model=PaginationResponseDTO[PublicProfileResponseDTO | MinimalProfileResponseDTO], status_code=status.HTTP_200_OK)
async def get_teachers(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: UserDTO = Depends(get_current_user),
    user_service: UsersService = Depends(get_user_service),
):
    total, items = await user_service.get_teachers(actor=current_user, limit=limit, offset=offset)
    return PaginationResponseDTO[PublicProfileResponseDTO | MinimalProfileResponseDTO](
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_me(user: UserDTO = Depends(get_current_user)):
    return user


@router.get("/{user_id}", response_model=PublicProfileResponseDTO | MinimalProfileResponseDTO, status_code=status.HTTP_200_OK)
async def get_public_profile(
    user_id: int,
    current_user: UserDTO = Depends(get_current_user),
    user_service: UsersService = Depends(get_user_service),
):
    return await user_service.get_public_profile(user_id=user_id, actor=current_user)


@router.patch("/{user_id}", response_model=TeachersResponseDTO | StudentsResponseDTO, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int,
    data: UpdateUserDataRequestDTO,
    current_user: UserDTO = Depends(get_current_user_with_target_permission),
    user_service: UsersService = Depends(get_user_service),
):
    return await user_service.update_user(user_id=user_id, data=data, actor=current_user)


@router.patch("/{user_id}/avatar", response_model=UserAvatarResponseDTO, status_code=status.HTTP_200_OK)
async def update_avatar(
    user_id: int,
    avatar: UploadFile = File(...),
    current_user: UserDTO = Depends(get_current_user_with_target_permission),
    user_service: UsersService = Depends(get_user_service),
):
    return await user_service.update_avatar(user_id=user_id, avatar=avatar, actor=current_user)


@router.delete("/{user_id}/avatar", status_code=status.HTTP_204_NO_CONTENT)
async def delete_avatar(
    user_id: int,
    current_user: UserDTO = Depends(get_current_user_with_target_permission),
    user_service: UsersService = Depends(get_user_service),
):
    await user_service.remove_avatar(actor=current_user, user_id=user_id)


@router.get("/{user_id}/avatar", response_class=FileResponse, status_code=status.HTTP_200_OK)
async def get_avatar(
    request: Request,
    user_id: int,
    current_user: UserDTO = Depends(get_current_user),
    service: UsersService = Depends(get_user_service),
):
    return await private_download(request, str(await service.avatar_file(current_user, user_id)), "avatar.webp", "image/webp")


@router.patch("/{user_id}/account-status", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def update_account_status(
    user_id: int,
    data: AdminAccountStatusRequestDTO,
    current_user: UserDTO = Depends(get_current_user),
    service: UsersService = Depends(get_user_service),
):
    return await service.update_account_status(current_user, user_id, data.is_active)


from src.modules.users.models_dto import UpdateSchoolGradeRequestDTO

@router.patch("/{user_id}/school-grade", response_model=PublicProfileResponseDTO | MinimalProfileResponseDTO, status_code=200)
async def update_school_grade(user_id: int, data: UpdateSchoolGradeRequestDTO,
    actor: UserDTO = Depends(get_current_user),
    service: UsersService = Depends(get_user_service)):
    return await service.update_school_grade(actor, user_id, data)
