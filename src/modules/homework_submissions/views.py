from typing import List, Optional
from fastapi import APIRouter, Request, Depends, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from starlette import status

from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.auth.depends import get_current_user
from src.modules.check_permission import get_current_teacher_user

from src.modules.homework_submissions.depends import get_homework_submissions_service
from src.modules.homework_submissions.models_dto import (
    HomeworkSubmissionResponseDTO,
    UpdateSubmissionStudentRequestDTO,
    UpdateSubmissionTeacherRequestDTO,
)
from src.modules.homework_submissions.service import HomeworkSubmissionsService
from src.modules.users.models_dto import UserDTO

router = APIRouter(tags=["Homework Submissions"])

@router.post(
    "/homeworks/{homework_id}/submissions",
    response_model=HomeworkSubmissionResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a homework attempt",
)
async def create_homework_submission(
    homework_id: int,
    text_content: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworkSubmissionsService = Depends(get_homework_submissions_service),
):
    return await service.create_submission(
        student_user_id=current_user.id,
        homework_id=homework_id,
        text_content=text_content,
        files=files,
    )

@router.get(
    "/homeworks/{homework_id}/submissions",
    response_model=PaginationResponseDTO[HomeworkSubmissionResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get all attempts for a homework",
)
async def get_homework_submissions(
    homework_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_date: str = Query("desc", description="Сортировка по дате (asc/desc)"),
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworkSubmissionsService = Depends(get_homework_submissions_service),
):
    return await service.get_submissions(
        user_id=current_user.id,
        user_role=current_user.role,
        homework_id=homework_id,
        limit=limit,
        offset=offset,
        sort_date=sort_date,
    )

@router.get(
    "/submissions/{submission_id}",
    response_model=HomeworkSubmissionResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get a specific attempt by ID",
)
async def get_homework_submission(
    submission_id: int,
    homework_id: int = Query(...), 
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworkSubmissionsService = Depends(get_homework_submissions_service),
):
    return await service.get_submission(
        user_id=current_user.id,
        user_role=current_user.role,
        homework_id=homework_id,
        submission_id=submission_id,
    )

@router.get(
    "/submissions/{submission_id}/files/{file_id}",
    status_code=status.HTTP_200_OK,
    summary="Download a specific file attached to an attempt",
)
async def get_homework_submission_file(
    submission_id: int,
    file_id: int,
    homework_id: int = Query(...),
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworkSubmissionsService = Depends(get_homework_submissions_service),
):
    file_record = await service.get_submission_file_download_path(
        user_id=current_user.id,
        user_role=current_user.role,
        homework_id=homework_id,
        submission_id=submission_id,
        file_id=file_id,
    )
    
    return FileResponse(
        path=file_record.pdf_file_path or file_record.original_file_path,
        media_type="application/pdf",
        filename=file_record.pdf_file_name or file_record.original_file_name,
    )

@router.patch(
    "/submissions/{submission_id}/student",
    response_model=HomeworkSubmissionResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update attempt as Student (Only if not CHECKED)",
)
async def update_homework_submission_student(
    request: Request,
    submission_id: int,
    homework_id: int = Query(...),
    text_content: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    expected_version: int | None = Form(None, ge=1),
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworkSubmissionsService = Depends(get_homework_submissions_service),
):
    form = await request.form()
    dto = UpdateSubmissionStudentRequestDTO(**({"text_content": text_content} if "text_content" in form else {}))
    return await service.update_submission_student(
        student_user_id=current_user.id,
        homework_id=homework_id,
        submission_id=submission_id,
        update_dto=dto,
        files=files, expected_version=expected_version,
    )

@router.patch(
    "/submissions/{submission_id}/teacher",
    response_model=HomeworkSubmissionResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update attempt as Teacher (Status, Grade, Comment)",
)
async def update_homework_submission_teacher(
    submission_id: int,
    data: UpdateSubmissionTeacherRequestDTO,
    homework_id: int = Query(...),
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: HomeworkSubmissionsService = Depends(get_homework_submissions_service),
):
    return await service.update_submission_teacher(
        teacher_user_id=current_user.id,
        homework_id=homework_id,
        submission_id=submission_id,
        update_dto=data,
    )

@router.delete(
    "/submissions/{submission_id}",
    response_model=HomeworkSubmissionResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Delete a submission",
)
async def delete_homework_submission(
    submission_id: int,
    homework_id: int = Query(...),
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworkSubmissionsService = Depends(get_homework_submissions_service),
):
    return await service.delete_submission(
        user_id=current_user.id,
        user_role=current_user.role,
        homework_id=homework_id,
        submission_id=submission_id,
    )


@router.post("/submissions/{submission_id}/submit", response_model=HomeworkSubmissionResponseDTO,
             status_code=status.HTTP_200_OK, summary="Submit the current answer (idempotent)")
async def submit_homework_submission(
    submission_id: int, homework_id: int = Query(...),
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworkSubmissionsService = Depends(get_homework_submissions_service),
):
    return await service.submit_submission(current_user.id, homework_id, submission_id)


@router.delete("/submissions/{submission_id}/files/{file_id}", response_model=HomeworkSubmissionResponseDTO,
               status_code=status.HTTP_200_OK, summary="Remove one answer attachment")
async def delete_submission_file(
    submission_id: int, file_id: int, homework_id: int = Query(...),
    expected_version: int | None = Query(None, ge=1),
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworkSubmissionsService = Depends(get_homework_submissions_service),
):
    return await service.mutate_file(current_user.id, homework_id, submission_id, file_id,
                                     expected_version=expected_version)


@router.put("/submissions/{submission_id}/files/{file_id}", response_model=HomeworkSubmissionResponseDTO,
            status_code=status.HTTP_200_OK, summary="Replace one answer attachment atomically")
async def replace_submission_file(
    submission_id: int, file_id: int, homework_id: int = Query(...),
    file: UploadFile = File(...), expected_version: int | None = Form(None, ge=1),
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworkSubmissionsService = Depends(get_homework_submissions_service),
):
    return await service.mutate_file(current_user.id, homework_id, submission_id, file_id, file,
                                     expected_version=expected_version)
