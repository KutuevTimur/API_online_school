from datetime import date
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from src.modules.check_permission import get_current_teacher_user
from src.modules.users.models_dto import UserDTO
from src.modules.teacher_planning.depends import get_teacher_planning_service
from src.modules.teacher_planning.service import TeacherPlanningService
from src.modules.teacher_planning.models_dto import NormRequestDTO, ReminderRequestDTO, PlanningStudentDTO, RecipientReminderDTO
from src.modules.base.orm_dto import PaginationResponseDTO

router = APIRouter(prefix='/teacher-planning', tags=['Teacher planning'])


class NormRevisionDTO(BaseModel):
    revision: int


@router.get('/students', response_model=PaginationResponseDTO[PlanningStudentDTO], status_code=200)
async def planning_students(week: date, deficit_only: bool = False, student_user_id: int | None = None, q: str | None = Query(None, max_length=100),
    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
    actor: UserDTO = Depends(get_current_teacher_user),
    service: TeacherPlanningService = Depends(get_teacher_planning_service)) -> PaginationResponseDTO[PlanningStudentDTO]:
    return await service.students(actor, week, q, limit, offset, student_user_id, deficit_only)


@router.put('/students/{student_user_id}/norm', response_model=NormRevisionDTO, status_code=200)
async def save_norm(student_user_id: int, data: NormRequestDTO,
    actor: UserDTO = Depends(get_current_teacher_user),
    service: TeacherPlanningService = Depends(get_teacher_planning_service)) -> dict[str, int]:
    return await service.norm(actor, student_user_id, data)


@router.get('/reminders', response_model=PaginationResponseDTO[RecipientReminderDTO], status_code=200)
async def reminders(lesson_id: int | None = None, student_user_id: int | None = None, only_missing: bool = True,
    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
    actor: UserDTO = Depends(get_current_teacher_user),
    service: TeacherPlanningService = Depends(get_teacher_planning_service)) -> PaginationResponseDTO[RecipientReminderDTO]:
    return await service.reminders(actor, lesson_id, student_user_id, limit, offset, only_missing)


@router.patch('/lessons/{lesson_id}/students/{student_user_id}', response_model=PaginationResponseDTO[RecipientReminderDTO], status_code=200)
async def mark_material_not_needed(lesson_id: int, student_user_id: int, data: ReminderRequestDTO,
    actor: UserDTO = Depends(get_current_teacher_user),
    service: TeacherPlanningService = Depends(get_teacher_planning_service)) -> PaginationResponseDTO[RecipientReminderDTO]:
    return await service.mark(actor, lesson_id, student_user_id, data)


from src.modules.teacher_planning.models_dto import LessonPriceDTO, UpdateLessonPriceDTO, WeeklyEarningsDTO


@router.get('/students/{student_user_id}/price', response_model=LessonPriceDTO, status_code=200)
async def student_price(student_user_id: int,
    actor: UserDTO = Depends(get_current_teacher_user),
    service: TeacherPlanningService = Depends(get_teacher_planning_service)) -> LessonPriceDTO:
    return await service.price(actor, student_user_id)


@router.put('/students/{student_user_id}/price', response_model=LessonPriceDTO, status_code=200)
async def save_student_price(student_user_id: int, data: UpdateLessonPriceDTO,
    actor: UserDTO = Depends(get_current_teacher_user),
    service: TeacherPlanningService = Depends(get_teacher_planning_service)) -> LessonPriceDTO:
    return await service.price(actor, student_user_id, data)


@router.get('/weekly-earnings', response_model=WeeklyEarningsDTO, status_code=200)
async def weekly_earnings(week: date,
    actor: UserDTO = Depends(get_current_teacher_user),
    service: TeacherPlanningService = Depends(get_teacher_planning_service)) -> WeeklyEarningsDTO:
    return await service.weekly_earnings(actor, week)
