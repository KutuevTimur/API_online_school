from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from starlette import status

from src.modules.auth.depends import get_current_user
from src.modules.check_permission import get_current_teacher_user
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
    description="Title and deadline are required. Description and file are optional."
)
async def create_homework(
    lesson_id: int = Form(...),
    student_user_id: int = Form(...),
    title: str = Form(...),
    deadline: datetime = Form(...),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: HomeworksService = Depends(get_homeworks_service),
):
    return await service.create_homework(
        teacher_user_id=current_user.id,
        lesson_id=lesson_id,
        student_user_id=student_user_id,
        title=title,
        deadline=deadline,
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
    "/{homework_id}/file",
    status_code=status.HTTP_200_OK,
    summary="Download a specific homework file (PDF)",
)
async def download_homework_file(
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
    
    return FileResponse(
        path=homework.pdf_file_path,
        media_type="application/pdf",
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
