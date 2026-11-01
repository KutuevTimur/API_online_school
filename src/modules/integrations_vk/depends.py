from typing import TYPE_CHECKING
from fastapi import Depends, Request

if TYPE_CHECKING:
    from src.modules.integrations_vk.booking_service import BookingService
from src.core.database.database import get_db
from src.modules.users.depends import get_user_service
from src.modules.integrations_vk.exception import IdentityError
from src.modules.integrations_vk.service import IdentityService


def get_identity_service(request: Request, session=Depends(get_db), users=Depends(get_user_service)) -> IdentityService:
    # Deliberately no credential/env bootstrap until F01.5 admission is implemented.
    if not getattr(request.app.state.config, 'vk_identity_enabled', False):
        raise IdentityError('CONNECTION_DISABLED', 403)
    return IdentityService(session, users)


async def require_connector() -> None:
    # F01.5 must replace this with verified credential/MAC admission. A raw subject,
    # bearer student JWT or arbitrary header cannot enable the connector boundary.
    raise IdentityError('AUTH_REQUIRED', 401)


def get_booking_service(identity: IdentityService = Depends(get_identity_service)) -> "BookingService":
    from src.modules.integrations_vk.booking_service import BookingService
    return BookingService(identity.session, identity.users, identity.clock)
