from typing import List
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import FileResponse
from starlette import status

from src.modules.auth.depends import get_current_user
from src.modules.check_permission import get_current_teacher_user
from src.modules.lectures.depends import get_lectures_service
from src.modules.lectures.models_dto import LectureResponseDTO
from src.modules.lectures.service import LecturesService
from src.modules.lesson_students.depends import get_lesson_students_service
from src.modules.lesson_students.models_dto import (
    AddStudentToLessonRequestDTO,
    CreateLessonStudentRequestDTO,
    LessonStudentResponseDTO
)
from src.modules.lesson_students.service import LessonStudentsService
from src.modules.users.models_dto import UserDTO

router = APIRouter(tags=["Lessons"])


@router.post(
    "/lessons/{lesson_id}/students",
    response_model=LessonStudentResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Add a student to a lesson",
)
async def add_student_to_lesson(
    lesson_id: int,
    data: AddStudentToLessonRequestDTO,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: LessonStudentsService = Depends(get_lesson_students_service),
):
    create_dto = CreateLessonStudentRequestDTO(
        lesson_id=lesson_id,
        student_user_id=data.student_user_id
    )
    return await service.add_student(teacher_user_id=current_user.id, data=create_dto)


@router.delete(
    "/lessons/{lesson_id}/students/{student_user_id}",
    response_model=LessonStudentResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Remove a student from a lesson",
)
async def remove_student_from_lesson(
    lesson_id: int,
    student_user_id: int,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: LessonStudentsService = Depends(get_lesson_students_service),
):
    return await service.remove_student(
        teacher_user_id=current_user.id,
        lesson_id=lesson_id,
        student_user_id=student_user_id,
    )


# --- Lectures ---

@router.post(
    "/lessons/{lesson_id}/students/{student_user_id}/lectures",
    response_model=LectureResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a lecture (PDF) for a student's lesson",
)
async def upload_lecture(
    lesson_id: int,
    student_user_id: int,
    file: UploadFile = File(...),
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: LecturesService = Depends(get_lectures_service),
):
    return await service.upload_lecture(
        teacher_user_id=current_user.id,
        lesson_id=lesson_id,
        student_user_id=student_user_id,
        file=file,
    )


@router.get(
    "/lessons/{lesson_id}/students/{student_user_id}/lectures",
    response_model=List[LectureResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get list of uploaded lectures for a student's lesson",
)
async def get_lectures(
    lesson_id: int,
    student_user_id: int,
    current_user: UserDTO = Depends(get_current_user),
    service: LecturesService = Depends(get_lectures_service),
):
    return await service.get_lectures(
        user_id=current_user.id,
        lesson_id=lesson_id,
        student_user_id=student_user_id,
    )


@router.get(
    "/lessons/{lesson_id}/students/{student_user_id}/lectures/{lecture_id}",
    status_code=status.HTTP_200_OK,
    summary="Download a specific lecture (PDF)",
)
async def download_lecture(
    lesson_id: int,
    student_user_id: int,
    lecture_id: int,
    current_user: UserDTO = Depends(get_current_user),
    service: LecturesService = Depends(get_lectures_service),
):
    lecture = await service.get_lecture_by_id(
        user_id=current_user.id,
        lesson_id=lesson_id,
        student_user_id=student_user_id,
        lecture_id=lecture_id,
    )
    
    return FileResponse(
        path=lecture.pdf_file_path,
        media_type="application/pdf",
        filename=lecture.pdf_file_name,
    )


@router.delete(
    "/lessons/{lesson_id}/students/{student_user_id}/lectures/{lecture_id}",
    response_model=LectureResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Delete a specific lecture",
)
async def delete_lecture(
    lesson_id: int,
    student_user_id: int,
    lecture_id: int,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: LecturesService = Depends(get_lectures_service),
):
    return await service.delete_lecture(
        teacher_user_id=current_user.id,
        lesson_id=lesson_id,
        student_user_id=student_user_id,
        lecture_id=lecture_id,
    )
