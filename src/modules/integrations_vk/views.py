from typing import Annotated, Literal
from uuid import UUID
from fastapi import APIRouter, Depends, Header, Response, Query, Request
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

async def no_store(response: Response) -> None:
    response.headers['Cache-Control'] = 'no-store'


router = APIRouter(tags=['VK integration (local F01.2–F01.3)'], dependencies=[Depends(no_store)])
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


from datetime import date
from src.modules.integrations_vk.depends import get_booking_service, get_booking_read_service
from src.modules.integrations_vk.booking_service import BookingService
from src.modules.integrations_vk.models_dto import (
    PublishWindowsRequest, PrepareBookingRequest, ConfirmBookingRequest,
    MaterializeRequest, BookingResolveRequest, BookingView, WindowView, WindowsPage, BookingsPage, PreparedBookingResponse,
)
BookingAPI = Annotated[BookingService, Depends(get_booking_service)]
BookingReadAPI = Annotated[BookingService, Depends(get_booking_read_service)]


@router.post('/teacher-planning/booking-windows', response_model=OperationResult, status_code=200, dependencies=mutations)
async def publish_windows(data: PublishWindowsRequest, service: BookingAPI, actor: Actor) -> OperationResult:
    return await service.publish(actor.id, data)


@router.get('/teacher-planning/booking-windows', response_model=WindowsPage, status_code=200)
async def list_windows(connection_id: UUID, week_start: date, service: BookingReadAPI, actor: Actor,
                       cursor: UUID | None = None, limit: int = Query(25, ge=1, le=100)) -> WindowsPage:
    return await service.list_windows(actor.id, connection_id, week_start, cursor, limit)


@router.post('/teacher-planning/booking-windows/{id}/close', response_model=OperationResult, status_code=200, dependencies=mutations)
async def close_window(id: UUID, data: RevisionRequest, service: BookingAPI, actor: Actor) -> OperationResult:
    return await service.close(actor.id, id, data)


@router.get('/teacher-planning/bookings', response_model=BookingsPage, status_code=200)
async def list_bookings(connection_id: UUID, week_start: date, service: BookingReadAPI, actor: Actor,
                        cursor: UUID | None = None, limit: int = Query(25, ge=1, le=100)) -> BookingsPage:
    return await service.list_bookings(actor.id, connection_id, week_start, cursor, limit)


@router.get('/teacher-planning/booking-calendar', response_model=BookingsPage, status_code=200)
async def booking_calendar(week_start: date, service: BookingReadAPI, actor: Actor) -> BookingsPage:
    return await service.calendar(actor.id, week_start)


@router.get('/teacher-planning/bookings/{id}', response_model=BookingView, status_code=200)
async def get_booking(id: UUID, service: BookingReadAPI, actor: Actor) -> BookingView:
    return await service.booking_view(actor.id, id)


@router.post('/teacher-planning/bookings/{id}/materialize', response_model=OperationResult, status_code=200, dependencies=mutations)
async def materialize_booking(id: UUID, data: MaterializeRequest, service: BookingAPI, actor: Actor) -> OperationResult:
    return await service.materialize(actor.id, id, data)


@router.post('/teacher-planning/bookings/{id}/resolve-invite', response_model=ResolveResponse, status_code=200, dependencies=mutations)
async def resolve_booking(id: UUID, data: BookingResolveRequest, service: BookingAPI, actor: Actor) -> ResolveResponse:
    return await service.resolve_booking(actor.id, id, data)


@router.post('/integrations/vk/interactions', response_model=PreparedBookingResponse, status_code=200, dependencies=[Depends(require_connector)])
async def prepare_booking(data: PrepareBookingRequest, service: BookingAPI) -> dict:
    return await service.prepare(data)


@router.post('/integrations/vk/bookings/confirm', response_model=OperationResult, status_code=200, dependencies=[Depends(require_connector)])
async def confirm_booking(data: ConfirmBookingRequest, service: BookingAPI) -> OperationResult:
    return await service.confirm_booking(data)


@router.get('/integrations/vk/operations/{id}', response_model=OperationResult, status_code=200, dependencies=[Depends(require_connector)])
async def booking_operation(id: UUID, actor_context: str, service: BookingAPI) -> OperationResult:
    return await service.connector_receipt(actor_context, id)


@router.get('/integrations/vk/windows', response_model=list[WindowView], status_code=200, dependencies=[Depends(require_connector)])
async def available_windows(actor_context: str, teacher_user_id: int, week_start: date, service: BookingAPI) -> list[WindowView]:
    return await service.available_windows(actor_context, teacher_user_id, week_start)


from src.modules.integrations_vk.models_dto import PlanningCapabilities


@router.get('/teacher-planning/booking-capabilities', response_model=PlanningCapabilities, status_code=200)
async def booking_capabilities(request: Request, actor: Actor, service: BookingReadAPI) -> PlanningCapabilities:
    return await service.capabilities(actor.id, getattr(request.app.state.config, 'vk_identity_enabled', False))


@router.get('/teacher-planning/linked-bookings', response_model=BookingsPage, status_code=200)
async def linked_bookings(connection_id: UUID, student_user_id: int, service: BookingReadAPI, actor: Actor,
                          cursor: UUID | None = None, limit: int = Query(25, ge=1, le=100)) -> BookingsPage:
    return await service.linked_bookings(actor.id, connection_id, student_user_id, cursor, limit)
