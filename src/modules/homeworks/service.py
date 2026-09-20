import os
import uuid
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.check_permission.exception import PermissionErrorService
from src.modules.handlers_files.handler_documents import HandlerDocuments
from src.modules.homeworks.exception import HomeworkNotFound
from src.modules.homeworks.models_dto import CreateHomeworkRequestDTO, HomeworkResponseDTO, HomeworkDTO
from src.modules.homeworks.repository import HomeworksRepository
from src.modules.lesson_students.repository import LessonStudentsRepository
from src.modules.lessons.repository import LessonsRepository
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository
from src.modules.path_builder.service import PathBuilder


class HomeworksService:
    def __init__(
        self,
        homeworks_repo: HomeworksRepository,
        lesson_students_repo: LessonStudentsRepository,
        lessons_repo: LessonsRepository,
        student_repo: StudentRepository,
        teacher_repo: TeacherRepository,
        path_builder: PathBuilder,
        handler_documents: HandlerDocuments,
        session_db: AsyncSession,
    ):
        self.homeworks_repo = homeworks_repo
        self.lesson_students_repo = lesson_students_repo
        self.lessons_repo = lessons_repo
        self.student_repo = student_repo
        self.teacher_repo = teacher_repo
        self.path_builder = path_builder
        self.handler_documents = handler_documents
        self.session_db = session_db

    async def _get_and_check_lesson_student(
        self,
        teacher_user_id: int,
        lesson_id: int,
        student_user_id: int,
    ):
        teacher = await self.teacher_repo.get_teacher_by_user_id(teacher_user_id)
        if not teacher:
            raise PermissionErrorService("Teacher user not found")

        lesson = await self.lessons_repo.get_lesson_by_id(lesson_id)
        if not lesson:
            raise PermissionErrorService("Lesson not found")

        if lesson.teacher_id != teacher.id:
            raise PermissionErrorService("You do not have permission to modify this lesson")

        student = await self.student_repo.get_student_by_user_id(student_user_id)
        if not student:
            raise PermissionErrorService("Student user not found")

        lesson_student = await self.lesson_students_repo.get_by_lesson_and_student(
            lesson_id=lesson.id,
            student_id=student.id
        )
        if not lesson_student:
            raise PermissionErrorService("Student is not enrolled in this lesson")

        return lesson_student

    async def create_homework(
        self,
        teacher_user_id: int,
        lesson_id: int,
        student_user_id: int,
        title: str,
        deadline: datetime,
        description: Optional[str] = None,
        file: Optional[UploadFile] = None,
    ) -> HomeworkResponseDTO:
        lesson_student = await self._get_and_check_lesson_student(
            teacher_user_id=teacher_user_id,
            lesson_id=lesson_id,
            student_user_id=student_user_id,
        )

        has_file = file is not None and file.filename != ""
        file_name = Path(file.filename).stem if has_file else None
        file_type = Path(file.filename).suffix.lstrip('.') if has_file else None

        dto = CreateHomeworkRequestDTO(
            lesson_student_id=lesson_student.id,
            title=title,
            description=description,
            deadline=deadline,
            original_file_path="",
            original_file_name=f"{file_name}.{file_type}" if file_name else None,
            original_file_type=file_type,
            pdf_file_path="",
            pdf_file_name=f"{file_name}.pdf" if file_name else None,
        )

        if not has_file:
            dto.original_file_path = None
            dto.pdf_file_path = None

        homework = await self.homeworks_repo.add_homework(dto)
        await self.session_db.flush()

        if has_file:
            original_dest = self.path_builder.get_homework_original(
                homework_id=homework.id,
                file_name=file_name,
                file_type=file_type,
            )
            pdf_dest = self.path_builder.get_homework_pdf(
                homework_id=homework.id,
                file_name=file_name,
            )

            original_path, pdf_path = await self.handler_documents.save_document(
                document=file,
                original_dest=original_dest,
                pdf_dest=pdf_dest,
            )

            homework = await self.homeworks_repo.update_homework_paths(
                homework_id=homework.id,
                original_file_path=str(original_path),
                pdf_file_path=str(pdf_path),
            )

        await self.session_db.commit()
        await self.session_db.refresh(homework)
        
        return HomeworkResponseDTO.model_validate(homework)

    async def get_homeworks(
        self,
        user_id: int,
        lesson_id: int,
        student_user_id: int,
    ) -> List[HomeworkResponseDTO]:
        student = await self.student_repo.get_student_by_user_id(student_user_id)
        if not student:
            raise PermissionErrorService("Student user not found")

        lesson_student = await self.lesson_students_repo.get_by_lesson_and_student(
            lesson_id=lesson_id,
            student_id=student.id
        )
        if not lesson_student:
            raise PermissionErrorService("Student is not enrolled in this lesson")

        teacher = await self.teacher_repo.get_teacher_by_user_id(user_id)
        lesson = await self.lessons_repo.get_lesson_by_id(lesson_id)
        
        is_teacher_owner = teacher and lesson and lesson.teacher_id == teacher.id
        is_student_owner = student_user_id == user_id

        if not is_teacher_owner and not is_student_owner:
            raise PermissionErrorService("Access denied to view these homeworks")

        homeworks = await self.homeworks_repo.get_all_by_lesson_student_id(lesson_student.id)
        return [HomeworkResponseDTO.model_validate(h) for h in homeworks]

    async def get_my_homeworks(self, student_user_id: int) -> List[HomeworkResponseDTO]:
        student = await self.student_repo.get_student_by_user_id(student_user_id)
        if not student:
            raise PermissionErrorService("Student user not found")
            
        homeworks = await self.homeworks_repo.get_all_by_student_id(student.id)
        return [HomeworkResponseDTO.model_validate(h) for h in homeworks]

    async def get_homework_file(
        self,
        user_id: int,
        lesson_id: int,
        student_user_id: int,
        homework_id: int,
    ) -> HomeworkDTO:
        student = await self.student_repo.get_student_by_user_id(student_user_id)
        if not student:
            raise PermissionErrorService("Student user not found")

        lesson_student = await self.lesson_students_repo.get_by_lesson_and_student(
            lesson_id=lesson_id,
            student_id=student.id
        )
        if not lesson_student:
            raise PermissionErrorService("Student is not enrolled in this lesson")

        teacher = await self.teacher_repo.get_teacher_by_user_id(user_id)
        lesson = await self.lessons_repo.get_lesson_by_id(lesson_id)
        
        is_teacher_owner = teacher and lesson and lesson.teacher_id == teacher.id
        is_student_owner = student_user_id == user_id

        if not is_teacher_owner and not is_student_owner:
            raise PermissionErrorService("Access denied to view this homework")

        homework = await self.homeworks_repo.get_by_id(homework_id)
        if not homework or homework.lesson_student_id != lesson_student.id:
            raise HomeworkNotFound("Homework not found")
            
        if not homework.pdf_file_path:
            raise HomeworkNotFound("No files attached to this homework")

        return HomeworkDTO.model_validate(homework)

    async def delete_homework(
        self,
        teacher_user_id: int,
        lesson_id: int,
        student_user_id: int,
        homework_id: int,
    ) -> HomeworkResponseDTO:
        lesson_student = await self._get_and_check_lesson_student(
            teacher_user_id=teacher_user_id,
            lesson_id=lesson_id,
            student_user_id=student_user_id,
        )

        homework = await self.homeworks_repo.get_by_id(homework_id)
        if not homework or homework.lesson_student_id != lesson_student.id:
            raise HomeworkNotFound("Homework does not exist")

        deleted = await self.homeworks_repo.delete_homework(homework.id)
        await self.session_db.commit()
        
        try:
            if deleted.original_file_path and os.path.exists(deleted.original_file_path):
                os.remove(deleted.original_file_path)
            if deleted.pdf_file_path and os.path.exists(deleted.pdf_file_path) and deleted.original_file_path != deleted.pdf_file_path:
                os.remove(deleted.pdf_file_path)
        except Exception:
            pass 

        return HomeworkResponseDTO.model_validate(deleted)
