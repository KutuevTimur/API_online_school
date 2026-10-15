from fastapi import APIRouter, Depends, Request
from src.modules.auth.depends import get_current_user
from src.modules.users.models_dto import UserDTO
from src.modules.account_invitations.depends import get_invitation_service
from src.modules.account_invitations.service import InvitationService
from src.modules.account_invitations.models_dto import (
    IssueInvitationRequest, ConsumeInvitationRequest, InvitationResponse, ConsumeInvitationResponse)
from src.modules.account_invitations.rate_limit import check_rate_limit

router = APIRouter(prefix="/account_invitations", tags=["Account access"])


@router.post("/issue", response_model=InvitationResponse, status_code=200)
async def issue(data: IssueInvitationRequest, request: Request,
                actor: UserDTO = Depends(get_current_user),
                service: InvitationService = Depends(get_invitation_service)):
    await check_rate_limit(request, "issue", str(data.user_id))
    return await service.issue(data.user_id, data.purpose, actor)


@router.post("/consume", response_model=ConsumeInvitationResponse, status_code=200)
async def consume(data: ConsumeInvitationRequest, request: Request,
                  service: InvitationService = Depends(get_invitation_service)):
    await check_rate_limit(request, "consume", data.token)
    return await service.consume(data.token, data.purpose, data.new_password)
