from fastapi import APIRouter, Depends
from src.modules.auth.depends import get_current_user
from src.modules.check_permission import get_current_teacher_user
from src.modules.homework_placements.depends import get_homework_placements_service
from src.modules.homework_placements.models_dto import AddDebtRequestDTO, PlacementResponseDTO
from src.modules.homework_placements.service import HomeworkPlacementsService
from src.modules.users.models_dto import UserDTO

router = APIRouter(prefix="/homeworks", tags=["Homework placements"])


@router.post("/{homework_id}/debts", response_model=PlacementResponseDTO, status_code=201)
async def add_homework_debt(
    homework_id: int, data: AddDebtRequestDTO,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: HomeworkPlacementsService = Depends(get_homework_placements_service),
) -> PlacementResponseDTO:
    return await service.add_debt(current_user.id, homework_id, data.lesson_id)


@router.get("/{homework_id}/placements", response_model=list[PlacementResponseDTO], status_code=200)
async def homework_placement_history(
    homework_id: int, current_user: UserDTO = Depends(get_current_user),
    service: HomeworkPlacementsService = Depends(get_homework_placements_service),
) -> list[PlacementResponseDTO]:
    return await service.history(current_user.id, homework_id)
