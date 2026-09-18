from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from starlette import status

from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.auth.depends import get_current_user
from src.modules.check_permission import get_current_teacher_user

from src.modules.homework_submissions.depends import get_homework_submissions_service
from src.modules.homework_submissions.models import HomeworkSubmissionStatus
from src.modules.homework_submissions.models_dto import (
    HomeworkSubmissionResponseDTO,
    UpdateSubmissionStudentRequestDTO,
    UpdateSubmissionTeacherRequestDTO,
)
from src.modules.homework_submissions.service import HomeworkSubmissionsService

from src.modules.homeworks.depends import get_homeworks_service
from src.modules.homeworks.models_dto import HomeworkResponseDTO
from src.modules.homeworks.service import HomeworksService
from src.modules.lectures.depends import get_lectures_service
from src.modules.lectures.models_dto import LectureResponseDTO
from src.modules.lectures.service import LecturesService
from src.modules.lessons.depends import get_lessons_service
from src.modules.lessons.models_dto import LessonResponseDTO, CreateLessonRequestDTO, UpdateLessonRequestDTO
from src.modules.lessons.service import LessonsService
from src.modules.lesson_students.depends import get_lesson_students_service
from src.modules.lesson_students.models_dto import (
    AddStudentToLessonRequestDTO,
    CreateLessonStudentRequestDTO,
    LessonStudentResponseDTO
)
from src.modules.lesson_students.service import LessonStudentsService
from src.modules.users.models_dto import UserDTO

router = APIRouter(tags=["Lessons"])


# --- Lessons CRUD ---

@router.post(
    "/lessons",
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
    "/lessons",
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
    "/lessons/{lesson_id}",
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
    "/lessons/{lesson_id}",
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
    "/lessons/{lesson_id}",
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


# --- Lesson-Students (Users assigned to a lesson) ---

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
    response_model=PaginationResponseDTO[LectureResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get list of uploaded lectures for a student's lesson",
)
async def get_lectures_list(
    lesson_id: int,
    student_user_id: int,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    from_date: Optional[datetime] = Query(None, description="От даты"),
    to_date: Optional[datetime] = Query(None, description="До даты"),
    sort_date: str = Query("desc", description="Сортировка по дате (asc/desc)"),
    current_user: UserDTO = Depends(get_current_user),
    service: LecturesService = Depends(get_lectures_service),
):
    return await service.get_lectures(
        user_id=current_user.id,
        lesson_id=lesson_id,
        student_user_id=student_user_id,
        limit=limit,
        offset=offset,
        from_date=from_date,
        to_date=to_date,
        sort_date=sort_date,
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


# --- Homeworks ---

@router.post(
    "/lessons/{lesson_id}/students/{student_user_id}/homeworks",
    response_model=HomeworkResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Create a homework for a student's lesson",
    description="Title and deadline are required. Description and file are optional."
)
async def create_homework(
    lesson_id: int,
    student_user_id: int,
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
    "/lessons/{lesson_id}/students/{student_user_id}/homeworks",
    response_model=List[HomeworkResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get list of homeworks for a student's lesson",
)
async def get_homeworks_list(
    lesson_id: int,
    student_user_id: int,
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworksService = Depends(get_homeworks_service),
):
    return await service.get_homeworks(
        user_id=current_user.id,
        lesson_id=lesson_id,
        student_user_id=student_user_id,
    )


@router.get(
    "/lessons/{lesson_id}/students/{student_user_id}/homeworks/{homework_id}/file",
    status_code=status.HTTP_200_OK,
    summary="Download a specific homework file (PDF)",
)
async def download_homework_file(
    lesson_id: int,
    student_user_id: int,
    homework_id: int,
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
    "/lessons/{lesson_id}/students/{student_user_id}/homeworks/{homework_id}",
    response_model=HomeworkResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Delete a specific homework",
)
async def delete_homework(
    lesson_id: int,
    student_user_id: int,
    homework_id: int,
    current_user: UserDTO = Depends(get_current_teacher_user),
    service: HomeworksService = Depends(get_homeworks_service),
):
    return await service.delete_homework(
        teacher_user_id=current_user.id,
        lesson_id=lesson_id,
        student_user_id=student_user_id,
        homework_id=homework_id,
    )



# --- Homework Submissions ---

@router.post(
    "/lessons/{lesson_id}/students/{student_user_id}/homeworks/{homework_id}/submissions",
    response_model=HomeworkSubmissionResponseDTO,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a homework attempt",
)
async def create_homework_submission(
    lesson_id: int,
    student_user_id: int,
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
    "/lessons/{lesson_id}/students/{student_user_id}/homeworks/{homework_id}/submissions",
    response_model=PaginationResponseDTO[HomeworkSubmissionResponseDTO],
    status_code=status.HTTP_200_OK,
    summary="Get all attempts for a homework",
)
async def get_homework_submissions(
    lesson_id: int,
    student_user_id: int,
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
    "/lessons/{lesson_id}/students/{student_user_id}/homeworks/{homework_id}/submissions/{submission_id}",
    response_model=HomeworkSubmissionResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Get a specific attempt by ID",
)
async def get_homework_submission(
    lesson_id: int,
    student_user_id: int,
    homework_id: int,
    submission_id: int,
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
    "/lessons/{lesson_id}/students/{student_user_id}/homeworks/{homework_id}/submissions/{submission_id}/files/{file_id}",
    status_code=status.HTTP_200_OK,
    summary="Download a specific file attached to an attempt",
)
async def get_homework_submission_file(
    lesson_id: int,
    student_user_id: int,
    homework_id: int,
    submission_id: int,
    file_id: int,
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
    "/lessons/{lesson_id}/students/{student_user_id}/homeworks/{homework_id}/submissions/{submission_id}/student",
    response_model=HomeworkSubmissionResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update attempt as Student (Only if not CHECKED)",
)
async def update_homework_submission_student(
    lesson_id: int,
    student_user_id: int,
    homework_id: int,
    submission_id: int,
    text_content: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworkSubmissionsService = Depends(get_homework_submissions_service),
):
    dto = UpdateSubmissionStudentRequestDTO(text_content=text_content)
    return await service.update_submission_student(
        student_user_id=current_user.id,
        homework_id=homework_id,
        submission_id=submission_id,
        update_dto=dto,
        files=files,
    )


@router.patch(
    "/lessons/{lesson_id}/students/{student_user_id}/homeworks/{homework_id}/submissions/{submission_id}/teacher",
    response_model=HomeworkSubmissionResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Update attempt as Teacher (Status, Grade, Comment)",
)
async def update_homework_submission_teacher(
    lesson_id: int,
    student_user_id: int,
    homework_id: int,
    submission_id: int,
    data: UpdateSubmissionTeacherRequestDTO,
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
    "/lessons/{lesson_id}/students/{student_user_id}/homeworks/{homework_id}/submissions/{submission_id}",
    response_model=HomeworkSubmissionResponseDTO,
    status_code=status.HTTP_200_OK,
    summary="Delete a submission",
)
async def delete_homework_submission(
    lesson_id: int,
    student_user_id: int,
    homework_id: int,
    submission_id: int,
    current_user: UserDTO = Depends(get_current_user),
    service: HomeworkSubmissionsService = Depends(get_homework_submissions_service),
):
    return await service.delete_submission(
        user_id=current_user.id,
        user_role=current_user.role,
        homework_id=homework_id,
        submission_id=submission_id,
    )
