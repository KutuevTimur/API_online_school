from fastapi import APIRouter, Depends, UploadFile, File, Response
from starlette import status

from src.modules.auth.depends import get_current_user
from src.modules.check_permission import get_current_user_with_target_permission
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.students.models_dto import StudentsDTO
from src.modules.teachers.models_dto import TeachersDTO
from src.modules.users.depends import get_user_service
from src.modules.users.models import UserRole
from src.modules.users.models_dto import UserResponse, UserDTO, UpdateUserDataRequestDTO
from src.modules.users.service import UsersService

router = APIRouter(prefix="/users")


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def get_me(user: UserDTO = Depends(get_current_user)):
    return user


@router.patch("/{user_id}", response_model=TeachersDTO | StudentsDTO, status_code=status.HTTP_200_OK)
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

    await avatar.seek(0)  # Сбрасываем курсор в начало
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
