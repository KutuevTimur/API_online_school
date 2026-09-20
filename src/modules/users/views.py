from fastapi import APIRouter, Depends, UploadFile, File, Response, Query
from starlette import status

from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.auth.depends import get_current_user
from src.modules.check_permission import get_current_user_with_target_permission
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.check_permission.depends import get_current_teacher_user
from src.modules.students.models_dto import StudentsResponseDTO
from src.modules.teachers.models_dto import TeachersResponseDTO
from src.modules.users.depends import get_user_service
from src.modules.users.models import UserRole
from src.modules.users.models_dto import UserResponse, UserDTO, UpdateUserDataRequestDTO, PublicProfileResponseDTO
from src.modules.users.service import UsersService

router = APIRouter(prefix="/users",  tags=["User"])


@router.get("/students", response_model=PaginationResponseDTO[PublicProfileResponseDTO], status_code=status.HTTP_200_OK)
async def get_students(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: UserDTO = Depends(get_current_teacher_user),
    user_service: UsersService = Depends(get_user_service),
):
    total, items = await user_service.get_students(limit=limit, offset=offset)
    return PaginationResponseDTO[PublicProfileResponseDTO](
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/teachers", response_model=PaginationResponseDTO[PublicProfileResponseDTO], status_code=status.HTTP_200_OK)
async def get_teachers(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: UserDTO = Depends(get_current_user),
    user_service: UsersService = Depends(get_user_service),
):
    total, items = await user_service.get_teachers(limit=limit, offset=offset)
    return PaginationResponseDTO[PublicProfileResponseDTO](
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_me(user: UserDTO = Depends(get_current_user)):
    return user


@router.get("/{user_id}", response_model=PublicProfileResponseDTO, status_code=status.HTTP_200_OK)
async def get_public_profile(
    user_id: int,
    current_user: UserDTO = Depends(get_current_user),
    user_service: UsersService = Depends(get_user_service),
):
    return await user_service.get_public_profile(user_id=user_id)


@router.patch("/{user_id}", response_model=TeachersResponseDTO | StudentsResponseDTO, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int,
    data: UpdateUserDataRequestDTO,
    current_user: UserDTO = Depends(get_current_user_with_target_permission),
    user_service: UsersService = Depends(get_user_service),
):
    if data.is_active is not None and current_user.role != UserRole.TEACHER:
        raise PermissionErrorService()

    return await user_service.update_user(user_id=user_id, data=data)


@router.patch("/{user_id}/avatar", status_code=status.HTTP_200_OK)
async def update_avatar(
    user_id: int,
    avatar: UploadFile = File(...),
    current_user: UserDTO = Depends(get_current_user_with_target_permission),
    user_service: UsersService = Depends(get_user_service),
):
    file_bytes = await avatar.read()

    await avatar.seek(0)
    await user_service.update_avatar(user_id=user_id, avatar=avatar)

    return Response(
        content=file_bytes,
        media_type=avatar.content_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'inline; filename="{avatar.filename}"'
        }
    )


@router.delete("/{user_id}/avatar", status_code=status.HTTP_204_NO_CONTENT)
async def delete_avatar(
    user_id: int,
    current_user: UserDTO = Depends(get_current_user_with_target_permission),
    user_service: UsersService = Depends(get_user_service),
):
    user_service.delete_avatar(user_id=user_id)
