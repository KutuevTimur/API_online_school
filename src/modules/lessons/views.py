from src.modules.base.list_query import ListView
from typing import Optional
from pydantic import AwareDatetime
from src.modules.lessons.models import LessonStatus
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

from uuid import UUID
from src.modules.lessons.depends import get_regular_lessons_service
from src.modules.lessons.service import RegularLessonsService
from src.modules.lessons.models_dto import (
    PreviewRegularLessonsRequestDTO, ConfirmRegularLessonsRequestDTO,
    RegularOperationResponseDTO, RegularSeriesResponseDTO,
)


@router.post("/regular/previews", response_model=RegularOperationResponseDTO, status_code=200)
async def preview_regular_lessons(
    data: PreviewRegularLessonsRequestDTO,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: RegularLessonsService = Depends(get_regular_lessons_service),
) -> RegularOperationResponseDTO:
    return await service.preview_regular(current_user.id, data)


@router.get("/regular/operations/{operation_id}", response_model=RegularOperationResponseDTO, status_code=200)
async def get_regular_operation(
    operation_id: UUID,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: RegularLessonsService = Depends(get_regular_lessons_service),
) -> RegularOperationResponseDTO:
    return await service.get_operation(current_user.id, operation_id)


@router.post("/regular/operations/{operation_id}/confirm", response_model=RegularOperationResponseDTO, status_code=200)
async def confirm_regular_lessons(
    operation_id: UUID, data: ConfirmRegularLessonsRequestDTO,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: RegularLessonsService = Depends(get_regular_lessons_service),
) -> RegularOperationResponseDTO:
    return await service.confirm_regular(current_user.id, operation_id, data)


@router.get("/regular/series/{series_id}", response_model=RegularSeriesResponseDTO, status_code=200)
async def get_regular_series(
    series_id: UUID,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: RegularLessonsService = Depends(get_regular_lessons_service),
) -> RegularSeriesResponseDTO:
    return await service.get_series(current_user.id, series_id)


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
    from_date: Optional[AwareDatetime] = Query(None, description="От даты"),
    to_date: Optional[AwareDatetime] = Query(None, description="До даты"),
    course_id: Optional[int] = Query(None, description="Фильтр по курсу"),
    lesson_status: LessonStatus | None = Query(None, alias="status"),
    view: ListView = Query(ListView.ALL),
    student_user_id: int | None = Query(None),
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
        lesson_status=lesson_status, view=view, student_user_id=student_user_id,
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
