from fastapi import APIRouter, Depends, Query, Path
from src.modules.auth.depends import get_current_user
from src.modules.users.models_dto import UserDTO
from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.notifications.depends import get_notifications_service
from src.modules.notifications.service import NotificationsService
from src.modules.notifications.models_dto import NotificationResponseDTO, UnreadCountDTO, NotificationTargetDTO

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=PaginationResponseDTO[NotificationResponseDTO], status_code=200)
async def notifications(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
    unread_only: bool = False, user: UserDTO = Depends(get_current_user),
    service: NotificationsService = Depends(get_notifications_service)) -> PaginationResponseDTO[NotificationResponseDTO]:
    return await service.page(user.id, limit, offset, unread_only)


@router.get("/unread", response_model=UnreadCountDTO, status_code=200)
async def unread(user: UserDTO = Depends(get_current_user),
    service: NotificationsService = Depends(get_notifications_service)) -> UnreadCountDTO:
    return await service.unread(user.id)


@router.patch("/{notification_id}/read", response_model=NotificationResponseDTO, status_code=200)
async def mark_read(notification_id: int = Path(gt=0), user: UserDTO = Depends(get_current_user),
    service: NotificationsService = Depends(get_notifications_service)) -> NotificationResponseDTO:
    return await service.mark_read(user.id, notification_id)


@router.get("/{notification_id}/target", response_model=NotificationTargetDTO, status_code=200)
async def target(notification_id: int = Path(gt=0), user: UserDTO = Depends(get_current_user),
    service: NotificationsService = Depends(get_notifications_service)) -> NotificationTargetDTO:
    return await service.target(user.id, notification_id)
