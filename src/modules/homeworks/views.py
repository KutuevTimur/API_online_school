from src.modules.base.list_query import ListView
from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.homeworks.models_dto import HomeworkListStatus
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query, Request, HTTPException
from src.modules.storage.download import private_download
from starlette import status

from src.modules.auth.depends import get_current_user
from src.modules.check_permission import get_current_teacher_user, get_current_student_user
from src.modules.homeworks.depends import get_homeworks_service
from src.modules.homeworks.models_dto import HomeworkResponseDTO
from src.modules.homeworks.service import HomeworksService
from src.modules.users.models_dto import UserDTO

router = APIRouter(prefix="/homeworks", tags=["Homeworks"])

@router.post(
    "",
    response_model=HomeworkResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a homework for a student's lesson",
    description="Deadline follows the next lesson of this course and student. Manual deadline is unavailable."
)
async def create_homework(
    request: Request,
    lesson_id: int = Form(...),
    student_user_id: int = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: HomeworksService = Depends(get_homeworks_service),
):
    if "deadline" in await request.form():
        raise HTTPException(status_code=422, detail="Manual deadline is unavailable")
    return await service.create_homework(
        teacher_user_id=current_user.id,
        lesson_id=lesson_id,
        student_user_id=student_user_id,
        title=title,
        description=description,
        file=file,
    )

@router.get(
    "",
    response_model=List[HomeworkResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get list of homeworks for a student's lesson",
)
async def get_homeworks_list(
    lesson_id: int = Query(...),
    student_user_id: int = Query(...),
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworksService = Depends(get_homeworks_service),
):
    return await service.get_homeworks(
        user_id=current_user.id,
        lesson_id=lesson_id,
        student_user_id=student_user_id,
    )

@router.get(
    "/my",
    response_model=List[HomeworkResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get all homeworks for the current student across all lessons",
)
async def get_my_homeworks(
    current_user: UserDTO = Depends(get_current_student_user),
    service: HomeworksService = Depends(get_homeworks_service),
):
    return await service.get_my_homeworks(
        student_user_id=current_user.id,
    )

@router.get(
    "/my/page",
    response_model=PaginationResponseDTO[HomeworkResponseDTO],
    status_code=status.HTTP_200_OK,
)
async def get_my_homeworks_page(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    course_id: int | None = Query(None),
    status_filter: HomeworkListStatus = Query(HomeworkListStatus.ALL, alias="status"),
    view: ListView = Query(ListView.ALL),
    overdue_only: bool = Query(False),
    current_user: UserDTO = Depends(get_current_student_user),
    service: HomeworksService = Depends(get_homeworks_service),
) -> PaginationResponseDTO[HomeworkResponseDTO]:
    return await service.get_my_page(current_user.id, limit, offset, course_id,
                                     status_filter, view, overdue_only)


@router.get("/available-debts", response_model=PaginationResponseDTO[HomeworkResponseDTO], status_code=200)
async def available_debts(
    lesson_id: int = Query(...), student_user_id: int = Query(...),
    limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworksService = Depends(get_homeworks_service),
) -> PaginationResponseDTO[HomeworkResponseDTO]:
    return await service.available_debts(current_user.id, lesson_id, student_user_id, limit, offset)


@router.get("/{homework_id}", response_model=HomeworkResponseDTO, status_code=200)
async def homework_detail(homework_id: int, current_user: UserDTO = Depends(get_current_user),
                          service: HomeworksService = Depends(get_homeworks_service)) -> HomeworkResponseDTO:
    return await service.detail(current_user.id, homework_id)


@router.get(
    "/{homework_id}/file",
    status_code=status.HTTP_200_OK,
    summary="Download a specific homework file (PDF)",
)
async def download_homework_file(
    request: Request,
    homework_id: int,
    lesson_id: int = Query(...),
    student_user_id: int = Query(...),
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworksService = Depends(get_homeworks_service),
):
    homework = await service.get_homework_file(
        user_id=current_user.id,
        lesson_id=lesson_id,
        student_user_id=student_user_id,
        homework_id=homework_id,
    )
    
    return await private_download(
        request=request,
        raw=homework.pdf_file_path,
        media_type=homework.download_mime,
        filename=homework.pdf_file_name,
    )

@router.delete(
    "/{homework_id}",
    response_model=HomeworkResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Delete a specific homework",
)
async def delete_homework(
    homework_id: int,
    lesson_id: int = Query(...),
    student_user_id: int = Query(...),
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: HomeworksService = Depends(get_homeworks_service),
):
    return await service.delete_homework(
        teacher_user_id=current_user.id,
        lesson_id=lesson_id,
        student_user_id=student_user_id,
        homework_id=homework_id,
    )
