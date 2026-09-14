import os
import uuid
from typing import List
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import UniqueViolationError

from src.modules.check_permission.exception import PermissionErrorService
from src.modules.handlers_files.handler_documents import HandlerDocuments
from src.modules.lectures.exception import LectureAlreadyExists, LectureNotFound
from src.modules.lectures.models_dto import CreateLectureRequestDTO, LectureResponseDTO, LectureDTO
from src.modules.lectures.repository import LecturesRepository
from src.modules.lesson_students.repository import LessonStudentsRepository
from src.modules.lessons.repository import LessonsRepository
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository
from src.modules.path_builder.service import PathBuilder


class LecturesService:
    def __init__(
        self,
        lectures_repo: LecturesRepository,
        lesson_students_repo: LessonStudentsRepository,
        lessons_repo: LessonsRepository,
        student_repo: StudentRepository,
        teacher_repo: TeacherRepository,
        path_builder: PathBuilder,
        handler_documents: HandlerDocuments,
        session_db: AsyncSession,
    ):
        self.lectures_repo = lectures_repo
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

    async def upload_lecture(
        self,
        teacher_user_id: int,
        lesson_id: int,
        student_user_id: int,
        file: UploadFile,
    ) -> LectureResponseDTO:
        lesson_student = await self._get_and_check_lesson_student(
            teacher_user_id=teacher_user_id,
            lesson_id=lesson_id,
            student_user_id=student_user_id,
        )

        file_name = Path(file.filename).stem if file.filename else uuid.uuid4().hex
        file_type = Path(file.filename).suffix.lstrip('.') if file.filename else "pdf"

        # 1. Создаем запись в БД, чтобы получить уникальный lecture_id
        dto = CreateLectureRequestDTO(
            lesson_student_id=lesson_student.id,
            original_file_path="",
            original_file_name=f"{file_name}.{file_type}",
            original_file_type=file_type,
            pdf_file_path="",
            pdf_file_name=f"{file_name}.pdf",
        )

        lecture = await self.lectures_repo.add_lecture(dto)
        await self.session_db.flush() # Получаем lecture.id

        # 2. Формируем пути используя lecture.id
        original_dest = self.path_builder.get_lecture_original(
            lecture_id=lecture.id,
            file_name=file_name,
            file_type=file_type,
        )
        pdf_dest = self.path_builder.get_lecture_pdf(
            lecture_id=lecture.id,
            file_name=file_name,
        )

        # 3. Сохраняем файл на диск
        original_path, pdf_path = await self.handler_documents.save_document(
            document=file,
            original_dest=original_dest,
            pdf_dest=pdf_dest,
        )

        # 4. Обновляем пути в БД
        updated_lecture = await self.lectures_repo.update_lecture_paths(
            lecture_id=lecture.id,
            original_file_path=str(original_path),
            pdf_file_path=str(pdf_path),
        )

        await self.session_db.commit()
        await self.session_db.refresh(updated_lecture)
        
        return LectureResponseDTO.model_validate(updated_lecture)

    async def get_lectures(
        self,
        user_id: int,
        lesson_id: int,
        student_user_id: int,
    ) -> List[LectureResponseDTO]:
        """Возвращает список лекций для занятия"""
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
        is_student_owner = student.user_id == user_id

        if not is_teacher_owner and not is_student_owner:
            raise PermissionErrorService("Access denied to view these lectures")

        lectures = await self.lectures_repo.get_all_by_lesson_student_id(lesson_student.id)
        return [LectureResponseDTO.model_validate(l) for l in lectures]

    async def get_lecture_by_id(
        self,
        user_id: int,
        lesson_id: int,
        student_user_id: int,
        lecture_id: int,
    ) -> LectureDTO:
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
        is_student_owner = student.user_id == user_id

        if not is_teacher_owner and not is_student_owner:
            raise PermissionErrorService("Access denied to view this lecture")

        lecture = await self.lectures_repo.get_by_id(lecture_id)
        if not lecture or lecture.lesson_student_id != lesson_student.id:
            raise LectureNotFound("Lecture not found")

        return LectureDTO.model_validate(lecture)

    async def delete_lecture(
        self,
        teacher_user_id: int,
        lesson_id: int,
        student_user_id: int,
        lecture_id: int,
    ) -> LectureResponseDTO:
        lesson_student = await self._get_and_check_lesson_student(
            teacher_user_id=teacher_user_id,
            lesson_id=lesson_id,
            student_user_id=student_user_id,
        )

        lecture = await self.lectures_repo.get_by_id(lecture_id)
        if not lecture or lecture.lesson_student_id != lesson_student.id:
            raise LectureNotFound("Lecture does not exist")

        deleted = await self.lectures_repo.delete_lecture(lecture.id)
        await self.session_db.commit()
        
        try:
            if os.path.exists(deleted.original_file_path):
                os.remove(deleted.original_file_path)
            if os.path.exists(deleted.pdf_file_path) and deleted.original_file_path != deleted.pdf_file_path:
                os.remove(deleted.pdf_file_path)
        except Exception:
            pass 

        return LectureResponseDTO.model_validate(deleted)
