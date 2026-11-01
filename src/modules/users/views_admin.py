from fastapi import APIRouter, Depends, Path, Query
from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.check_permission.depends import get_current_admin_user
from src.modules.users.depends import get_user_service
from src.modules.users.models import UserRole
from src.modules.users.models_dto import AdminUserResponseDTO, UserDTO
from src.modules.users.service import UsersService

admin_router = APIRouter(prefix="/admin/users", tags=["Admin users"])


@admin_router.get("", response_model=PaginationResponseDTO[AdminUserResponseDTO], status_code=200)
async def list_users(
    role: UserRole | None = None,
    is_active: bool | None = None,
    is_activated: bool | None = None,
    q: str | None = Query(None, min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=2147483647),
    actor: UserDTO = Depends(get_current_admin_user),
    service: UsersService = Depends(get_user_service),
) -> PaginationResponseDTO[AdminUserResponseDTO]:
    items, total = await service.admin_users(actor, role, is_active, is_activated, q, limit, offset)
    return PaginationResponseDTO(items=items, total=total, limit=limit, offset=offset)


@admin_router.get("/{user_id}", response_model=AdminUserResponseDTO, status_code=200)
async def user_detail(
    user_id: int = Path(gt=0),
    actor: UserDTO = Depends(get_current_admin_user),
    service: UsersService = Depends(get_user_service),
) -> AdminUserResponseDTO:
    return await service.admin_user(actor, user_id)
