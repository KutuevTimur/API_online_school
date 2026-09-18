import os
from datetime import datetime, UTC
from pathlib import Path
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.handlers_files.handler_documents import HandlerDocuments
from src.modules.homework_submissions.exception import HomeworkSubmissionNotFound, HomeworkSubmissionNotEditable
from src.modules.homework_submissions.models import HomeworkSubmissionStatus
from src.modules.homework_submissions.models_dto import (
    HomeworkSubmissionResponseDTO,
    HomeworkSubmissionRequestDTO,
    HomeworkSubmissionFileRequestDTO,
    UpdateSubmissionTeacherRequestDTO,
    UpdateSubmissionStudentRequestDTO, UpdateSubmissionTeacherDTO,
)
from src.modules.homework_submissions.repository import HomeworkSubmissionsRepository
from src.modules.homeworks.repository import HomeworksRepository
from src.modules.path_builder.service import PathBuilder
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository
from src.modules.lesson_students.models import LessonStudent
from src.modules.lessons.models import Lesson
from src.modules.users.models import UserRole


class HomeworkSubmissionsService:
    def __init__(
        self,
        homework_submissions_repo: HomeworkSubmissionsRepository,
        homeworks_repo: HomeworksRepository,
        path_builder: PathBuilder,
        handler_documents: HandlerDocuments,
        teacher_repo: TeacherRepository,
        student_repo: StudentRepository,
        session_db: AsyncSession,
    ):
        self.homework_submissions_repo = homework_submissions_repo
        self.homeworks_repo = homeworks_repo
        self.path_builder = path_builder
        self.handler_documents = handler_documents
        self.teacher_repo = teacher_repo
        self.student_repo = student_repo
        self.session_db = session_db

    async def _check_access(self, user_id: int, user_role: UserRole, homework_id: int):
        """
        Проверяет доступ пользователя к домашней работе.
        
        :param user_id: ID пользователя.
        :param user_role: Роль (UserRole.STUDENT или UserRole.TEACHER).
        :param homework_id: ID домашней работы.
        :return: (homework, student_id, teacher_id)
        :raises HomeworkSubmissionNotFound: Если домашняя работа не найдена.
        :raises PermissionErrorService: Если нет прав доступа к данной дз.
        """
        homework = await self.homeworks_repo.get_by_id(homework_id)
        if not homework:
            raise HomeworkSubmissionNotFound("Homework not found")

        student_id = None
        teacher_id = None

        if user_role == UserRole.STUDENT:
            student = await self.student_repo.get_student_by_user_id(user_id)
            
            stmt = select(LessonStudent).where(LessonStudent.id == homework.lesson_student_id)
            lesson_student = await self.session_db.scalar(stmt)
            
            if not student or (lesson_student and lesson_student.student_id != student.id):
                raise PermissionErrorService("Access denied to this homework")
            student_id = student.id
        elif user_role == UserRole.TEACHER:
            teacher = await self.teacher_repo.get_teacher_by_user_id(user_id)
            
            stmt = select(Lesson).join(LessonStudent).where(LessonStudent.id == homework.lesson_student_id)
            lesson = await self.session_db.scalar(stmt)
            
            if not teacher or (lesson and lesson.teacher_id != teacher.id):
                raise PermissionErrorService("Access denied to this homework")
            teacher_id = teacher.id
        else:
            raise PermissionErrorService("Invalid role for checking homework access")

        return homework, student_id, teacher_id

    async def create_submission(
        self,
        student_user_id: int,
        homework_id: int,
        text_content: Optional[str] = None,
        files: Optional[List[UploadFile]] = None,
    ) -> HomeworkSubmissionResponseDTO:
        """
        Создает новую попытку сдачи домашней работы (студентом).

        :raises HomeworkSubmissionNotFound: Если ДЗ не найдено.
        :raises PermissionErrorService: Если нет доступа.
        """
        homework, student_id, _ = await self._check_access(student_user_id, UserRole.STUDENT, homework_id)

        max_attempt = await self.homework_submissions_repo.get_max_attempt_number(homework_id)
        attempt_number = max_attempt + 1

        submission_dto = HomeworkSubmissionRequestDTO(
            homework_id=homework_id,
            attempt_number=attempt_number,
            text_content=text_content,
            status=HomeworkSubmissionStatus.DRAFT,
            submitted_at=datetime.now(UTC).replace(tzinfo=None)
        )

        submission = await self.homework_submissions_repo.add_submission(submission_dto)
        await self.session_db.flush()

        if files:
            files_data = []
            for file in files:
                if not getattr(file, "filename", None):
                    continue
                file_name = Path(file.filename).stem
                file_type = Path(file.filename).suffix.lstrip('.')
                
                original_dest = self.path_builder.get_homework_submission_original(
                    homework_submission_id=submission.id,
                    file_name=file_name,
                    file_type=file_type,
                )
                pdf_dest = self.path_builder.get_homework_submission_pdf(
                    homework_submission_id=submission.id,
                    file_name=file_name,
                )
                
                original_path, pdf_path = await self.handler_documents.save_document(
                    document=file,
                    original_dest=original_dest,
                    pdf_dest=pdf_dest
                )
                
                files_data.append(HomeworkSubmissionFileRequestDTO(
                    submission_id=submission.id,
                    original_file_path=str(original_path),
                    original_file_name=f"{file_name}.{file_type}",
                    original_file_type=file_type,
                    pdf_file_path=str(pdf_path),
                    pdf_file_name=f"{file_name}.pdf",
                ))
            
            await self.homework_submissions_repo.add_submission_files(files_data)

        await self.session_db.commit()
        
        submission = await self.homework_submissions_repo.get_by_submission_id(submission.id)
        return HomeworkSubmissionResponseDTO.model_validate(submission)

    async def get_submissions(
        self,
        user_id: int,
        user_role: UserRole,
        homework_id: int,
        limit: int,
        offset: int,
        sort_date: str = "desc"
    ) -> PaginationResponseDTO[HomeworkSubmissionResponseDTO]:
        """
        Получает пагинированный список попыток для дз.
        
        :raises HomeworkSubmissionNotFound: Если ДЗ не найдено.
        :raises PermissionErrorService: Если нет доступа.
        """
        await self._check_access(user_id, user_role, homework_id)
        
        submissions, total = await self.homework_submissions_repo.get_submissions_by_homework_id(
            homework_id=homework_id,
            limit=limit,
            offset=offset,
            sort_date=sort_date
        )

        items = [HomeworkSubmissionResponseDTO.model_validate(sub) for sub in submissions]
        return PaginationResponseDTO(items=items, total=total, limit=limit, offset=offset)

    async def get_submission(
        self,
        user_id: int,
        user_role: UserRole,
        homework_id: int,
        submission_id: int,
    ) -> HomeworkSubmissionResponseDTO:
        """
        Получает данные конкретной попытки по её ID.
        
        :raises HomeworkSubmissionNotFound: Если попытка не найдена.
        :raises PermissionErrorService: Если нет доступа.
        """
        await self._check_access(user_id, user_role, homework_id)
        
        submission = await self.homework_submissions_repo.get_by_submission_id(submission_id)
        if not submission or submission.homework_id != homework_id:
            raise HomeworkSubmissionNotFound("Homework submission not found")
            
        return HomeworkSubmissionResponseDTO.model_validate(submission)

    async def update_submission_student(
        self,
        student_user_id: int,
        homework_id: int,
        submission_id: int,
        update_dto: UpdateSubmissionStudentRequestDTO,
        files: Optional[List[UploadFile]] = None,
    ) -> HomeworkSubmissionResponseDTO:
        """
        Обновляет текст и файлы попытки. Доступно только ученику.
        
        :raises HomeworkSubmissionNotFound: Если попытка не найдена.
        :raises PermissionErrorService: Если нет доступа.
        :raises HomeworkSubmissionNotEditable: Если попытка уже проверена учителем.
        """
        _, _, _ = await self._check_access(student_user_id, UserRole.STUDENT, homework_id)
        
        submission = await self.homework_submissions_repo.get_by_submission_id(submission_id)
        if not submission or submission.homework_id != homework_id:
            raise HomeworkSubmissionNotFound("Homework submission not found")
            
        if submission.status == HomeworkSubmissionStatus.CHECKED:
            raise HomeworkSubmissionNotEditable("Cannot edit checked submission")

        update_data = update_dto.model_dump(exclude_unset=True)
            
        if update_data:
            update_data["updated_at"] = datetime.now(UTC).replace(tzinfo=None)
            await self.homework_submissions_repo.update_submission(submission_id, update_data)
        
        if files:
            old_files = await self.homework_submissions_repo.delete_submission_files(submission_id)
            await self.session_db.flush()
            for old_file in old_files:
                if old_file.original_file_path and os.path.exists(old_file.original_file_path):
                    os.remove(old_file.original_file_path)
                if old_file.pdf_file_path and os.path.exists(old_file.pdf_file_path) and old_file.original_file_path != old_file.pdf_file_path:
                    os.remove(old_file.pdf_file_path)
                    
            files_data = []
            for file in files:
                if not getattr(file, "filename", None):
                    continue
                file_name = Path(file.filename).stem
                file_type = Path(file.filename).suffix.lstrip('.')
                
                original_dest = self.path_builder.get_homework_submission_original(
                    homework_submission_id=submission.id,
                    file_name=file_name,
                    file_type=file_type,
                )
                pdf_dest = self.path_builder.get_homework_submission_pdf(
                    homework_submission_id=submission.id,
                    file_name=file_name,
                )
                
                original_path, pdf_path = await self.handler_documents.save_document(
                    document=file,
                    original_dest=original_dest,
                    pdf_dest=pdf_dest
                )
                
                files_data.append(HomeworkSubmissionFileRequestDTO(
                    submission_id=submission.id,
                    original_file_path=str(original_path),
                    original_file_name=f"{file_name}.{file_type}",
                    original_file_type=file_type,
                    pdf_file_path=str(pdf_path),
                    pdf_file_name=f"{file_name}.pdf",
                ))
            
            await self.homework_submissions_repo.add_submission_files(files_data)

        await self.session_db.commit()
        
        submission = await self.homework_submissions_repo.get_by_submission_id(submission_id)
        return HomeworkSubmissionResponseDTO.model_validate(submission)

    async def update_submission_teacher(
        self,
        teacher_user_id: int,
        homework_id: int,
        submission_id: int,
        update_dto: UpdateSubmissionTeacherRequestDTO,
    ) -> HomeworkSubmissionResponseDTO:
        """
        Обновляет статус, оценку или комментарий к попытке. Доступно только учителю.
        
        :raises HomeworkSubmissionNotFound: Если попытка не найдена.
        :raises PermissionErrorService: Если нет доступа.
        """
        _, _, teacher_id = await self._check_access(teacher_user_id, UserRole.TEACHER, homework_id)
        
        submission = await self.homework_submissions_repo.get_by_submission_id(submission_id)
        if not submission or submission.homework_id != homework_id:
            raise HomeworkSubmissionNotFound("Homework submission not found")

        update_data = update_dto.model_dump(exclude_unset=True)

        if update_dto.status == HomeworkSubmissionStatus.CHECKED:
            update_data["checked_at"] = datetime.now(UTC).replace(tzinfo=None)
            update_data["checked_by"] = teacher_id
            
        if update_data:
            update_data["updated_at"] = datetime.now(UTC).replace(tzinfo=None)
            await self.homework_submissions_repo.update_submission(
                submission_id,
                update_data
            )
            await self.session_db.commit()

        submission = await self.homework_submissions_repo.get_by_submission_id(submission_id)
        return HomeworkSubmissionResponseDTO.model_validate(submission)

    async def delete_submission(
        self,
        user_id: int,
        user_role: UserRole,
        homework_id: int,
        submission_id: int,
    ) -> HomeworkSubmissionResponseDTO:
        """
        Удаляет попытку с файлами. Ученик не может удалить проверенную работу.
        
        :raises HomeworkSubmissionNotFound: Если попытка не найдена.
        :raises PermissionErrorService: Если нет доступа.
        :raises HomeworkSubmissionNotEditable: Если ученик удаляет проверенную работу.
        """
        await self._check_access(user_id, user_role, homework_id)
        
        submission = await self.homework_submissions_repo.get_by_submission_id(submission_id)
        if not submission or submission.homework_id != homework_id:
            raise HomeworkSubmissionNotFound("Homework submission not found")
            
        if user_role == UserRole.STUDENT and submission.status == HomeworkSubmissionStatus.CHECKED:
            raise HomeworkSubmissionNotEditable("Cannot delete checked submission")

        old_files = submission.files
        for old_file in old_files:
            if old_file.original_file_path and os.path.exists(old_file.original_file_path):
                os.remove(old_file.original_file_path)
            if old_file.pdf_file_path and os.path.exists(old_file.pdf_file_path) and old_file.original_file_path != old_file.pdf_file_path:
                os.remove(old_file.pdf_file_path)

        dto = HomeworkSubmissionResponseDTO.model_validate(submission)
        await self.homework_submissions_repo.delete_submission(submission_id)
        await self.session_db.commit()
        return dto

    async def get_submission_file_download_path(
        self,
        user_id: int,
        user_role: UserRole,
        homework_id: int,
        submission_id: int,
        file_id: int
    ):
        """
        Получает путь файла для скачивания.
        
        :raises HomeworkSubmissionNotFound: Если файл или попытка не найдены.
        :raises PermissionErrorService: Если нет доступа.
        """
        await self._check_access(user_id, user_role, homework_id)
        submission = await self.homework_submissions_repo.get_by_submission_id(submission_id)
        
        if not submission or submission.homework_id != homework_id:
            raise HomeworkSubmissionNotFound("Homework submission not found")

        file_res = await self.homework_submissions_repo.get_submission_file_by_id(file_id)
        if not file_res or file_res.submission_id != submission_id:
            raise HomeworkSubmissionNotFound("Submission file not found")
            
        return file_res