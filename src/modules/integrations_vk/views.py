from typing import Annotated, Literal
from uuid import UUID
from fastapi import APIRouter, Depends, Header, Response
from src.modules.auth.browser import browser_guard
from src.modules.auth.depends import get_current_user
from src.modules.auth.login import oauth2_scheme
from src.modules.users.models_dto import UserDTO
from src.modules.integrations_vk.depends import get_identity_service, require_connector
from src.modules.integrations_vk.service import IdentityService
from src.modules.integrations_vk.models_dto import (
    IssueChallengeRequest, ClaimChallengeRequest, RevisionRequest, ResolveRecipientRequest,
    ChallengeResponse, IdentityStatus, OperationResult, ResolveResponse,
)

router = APIRouter(tags=['VK identity (local F01.2)'])
Service = Annotated[IdentityService, Depends(get_identity_service)]
Actor = Annotated[UserDTO, Depends(get_current_user)]
SessionKey = Annotated[str, Depends(oauth2_scheme)]
Reauth = Annotated[str, Header(alias='X-LGG-Reauth', min_length=1, max_length=1024)]
mutations = [Depends(browser_guard)]


@router.get('/users/me/integrations/vk', response_model=IdentityStatus, status_code=200)
async def status(response: Response, service: Service, actor: Actor, session: SessionKey) -> IdentityStatus:
    response.headers['Cache-Control'] = 'no-store'
    return await service.status(actor.id, session)


@router.post('/users/me/integrations/vk', response_model=ChallengeResponse, status_code=200, dependencies=mutations)
async def issue(data: IssueChallengeRequest, response: Response, service: Service, actor: Actor,
                session: SessionKey, password: Reauth) -> ChallengeResponse:
    response.headers['Cache-Control'] = 'no-store'
    return await service.issue_challenge(actor.id, session, password, data)


@router.post('/users/me/integrations/vk/challenges/{id}/confirm', response_model=OperationResult,
             status_code=200, dependencies=mutations)
async def confirm(id: UUID, data: RevisionRequest, response: Response, service: Service,
                  actor: Actor, session: SessionKey, password: Reauth) -> OperationResult:
    response.headers['Cache-Control'] = 'no-store'
    return await service.confirm_challenge(actor.id, session, password, id, data)


@router.delete('/users/me/integrations/vk', response_model=OperationResult, status_code=200, dependencies=mutations)
async def unlink(connection_id: UUID, data: RevisionRequest, response: Response, service: Service,
                 actor: Actor, session: SessionKey, password: Reauth) -> OperationResult:
    response.headers['Cache-Control'] = 'no-store'
    return await service.unlink(actor.id, session, password, connection_id, data)


@router.post('/integrations/vk/challenges/claim', response_model=OperationResult, status_code=200,
             dependencies=[Depends(require_connector)])
async def claim(data: ClaimChallengeRequest, response: Response, service: Service) -> OperationResult:
    response.headers['Cache-Control'] = 'no-store'
    return await service.claim_challenge(data)


@router.post('/teacher-planning/parent-grants/{id}/{decision}', response_model=OperationResult,
             status_code=200, dependencies=mutations)
async def decide(id: UUID, decision: Literal['confirm', 'reject', 'revoke'], data: RevisionRequest,
                 response: Response, service: Service, actor: Actor) -> OperationResult:
    response.headers['Cache-Control'] = 'no-store'
    return await service.decide_grant(actor.id, id, decision, data)


@router.post('/teacher-planning/recipients/{id}/resolve-invite', response_model=ResolveResponse,
             status_code=200, dependencies=mutations)
async def resolve(id: UUID, data: ResolveRecipientRequest, response: Response,
                  service: Service, actor: Actor) -> ResolveResponse:
    response.headers['Cache-Control'] = 'no-store'
    return await service.resolve_invite(actor.id, id, data)


@router.get('/users/me/integrations/vk/operations/{id}', response_model=OperationResult, status_code=200)
async def operation(id: UUID, action: str, response: Response, service: Service, actor: Actor) -> OperationResult:
    response.headers['Cache-Control'] = 'no-store'
    return await service.operation_status(actor.id, id, action)
