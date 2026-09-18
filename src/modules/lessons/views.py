from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from starlette import status

from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.auth.depends import get_current_user
from src.modules.check_permission import get_current_teacher_user
from src.modules.lessons.depends import get_lessons_service
from src.modules.lessons.models_dto import LessonResponseDTO, CreateLessonRequestDTO, UpdateLessonRequestDTO
from src.modules.lessons.service import LessonsService
from src.modules.users.models_dto import UserDTO

router = APIRouter(prefix="/lessons", tags=["Lessons"])

@router.post(
    "",
    response_model=LessonResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new lesson",
)
async def create_lesson(
    data: CreateLessonRequestDTO,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: LessonsService = Depends(get_lessons_service),
):
    return await service.create_lesson(
        teacher_user_id=current_user.id,
        data=data,
    )

@router.get(
    "",
    response_model=PaginationResponseDTO[LessonResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get list of lessons",
    description="Get lessons with pagination, date filtering, sorting and course_id filter. For students, returns enrolled lessons. For teachers, returns created lessons."
)
async def get_lessons(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    from_date: Optional[datetime] = Query(None, description="От даты"),
    to_date: Optional[datetime] = Query(None, description="До даты"),
    course_id: Optional[int] = Query(None, description="Фильтр по курсу"),
    sort_date: str = Query("desc", description="Сортировка по дате (asc/desc)"),
    current_user: UserDTO = Depends(get_current_user),
    service: LessonsService = Depends(get_lessons_service),
):
    return await service.get_lessons(
        current_user=current_user,
        limit=limit,
        offset=offset,
        from_date=from_date,
        to_date=to_date,
        course_id=course_id,
        sort_date=sort_date,
    )

@router.get(
    "/{lesson_id}",
    response_model=LessonResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get specific lesson",
)
async def get_lesson(
    lesson_id: int,
    current_user: UserDTO = Depends(get_current_user),
    service: LessonsService = Depends(get_lessons_service),
):
    return await service.get_lesson(
        current_user=current_user,
        lesson_id=lesson_id,
    )

@router.patch(
    "/{lesson_id}",
    response_model=LessonResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update a lesson",
)
async def update_lesson(
    lesson_id: int,
    data: UpdateLessonRequestDTO,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: LessonsService = Depends(get_lessons_service),
):
    return await service.update_lesson(
        teacher_user_id=current_user.id,
        lesson_id=lesson_id,
        data=data,
    )

@router.delete(
    "/{lesson_id}",
    response_model=LessonResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Delete a lesson",
)
async def delete_lesson(
    lesson_id: int,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: LessonsService = Depends(get_lessons_service),
):
    return await service.delete_lesson(
        teacher_user_id=current_user.id,
        lesson_id=lesson_id,
    )
