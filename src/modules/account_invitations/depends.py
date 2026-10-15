from fastapi import Depends
from src.modules.users.depends import get_user_service
from src.modules.users.service import UsersService
from src.modules.account_invitations.service import InvitationService


def get_invitation_service(users: UsersService = Depends(get_user_service)) -> InvitationService:
    return InvitationService(users)
