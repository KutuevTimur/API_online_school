from src.modules.files.service import FileAssetsService, atomic_file_upload
from src.modules.check_permission.service import ObjectPermissionService
import os
import uuid
from typing import List, Optional
from datetime import datetime
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.handlers_files.handler_documents import HandlerDocuments
from src.modules.lectures.exception import LectureNotFound
from src.modules.lectures.models_dto import CreateLectureRequestDTO, LectureResponseDTO, LectureDTO
from src.modules.lectures.repository import LecturesRepository
from src.modules.lesson_students.repository import LessonStudentsRepository
from src.modules.lessons.repository import LessonsRepository
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository
from src.modules.path_builder.service import PathBuilder
from src.modules.storage.download import safe_display_name


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
        return await ObjectPermissionService(self.session_db).recipient(
            teacher_user_id, lesson_id, student_user_id, write=True
        )

    @atomic_file_upload
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

        file_name = Path(safe_display_name(file.filename)).stem
        file_type = self.handler_documents._validate_extension(file.filename)

        dto = CreateLectureRequestDTO(
            lesson_student_id=lesson_student.id,
            original_file_path="",
            original_file_name=f"{file_name}.{file_type}",
            original_file_type=file_type,
            pdf_file_path="",
            pdf_file_name=f"{file_name}.pdf",
        )

        storage_name = uuid.uuid4().hex
        lecture = await self.lectures_repo.add_lecture(dto)
        await self.session_db.flush() 

        original_dest = self.path_builder.get_lecture_original(
            lecture_id=lecture.id,
            file_name=storage_name,
            file_type=file_type,
        )
        pdf_dest = self.path_builder.get_lecture_pdf(
            lecture_id=lecture.id,
            file_name=storage_name,
        )

        original_path, pdf_path = await self.handler_documents.save_document(
            document=file,
            original_dest=original_dest,
            pdf_dest=pdf_dest,
        )

        updated_lecture = await self.lectures_repo.update_lecture_paths(
            lecture_id=lecture.id,
            original_file_path=str(original_path),
            pdf_file_path=str(pdf_path),
        )

        updated_lecture.original_asset_id, updated_lecture.download_asset_id = await FileAssetsService(
            self.session_db, self.handler_documents).register(original_path, pdf_path, dto.original_file_name, teacher_user_id, student_user_id)
        updated_lecture.pdf_file_name = Path(dto.original_file_name).stem + pdf_path.suffix
        if updated_lecture.original_asset_id == updated_lecture.download_asset_id:
            updated_lecture.original_file_path = str(pdf_path)

        await self.session_db.commit()
        self.handler_documents.upload_committed = True
        await self.session_db.refresh(updated_lecture)
        
        return LectureResponseDTO.model_validate(updated_lecture)

    async def get_lectures(
        self,
        user_id: int,
        lesson_id: int,
        student_user_id: int,
        limit: int = 100,
        offset: int = 0,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sort_date: str = "desc",
    ) -> PaginationResponseDTO[LectureResponseDTO]:
        lesson_student = await ObjectPermissionService(self.session_db).recipient(
            user_id, lesson_id, student_user_id
        )

        lectures, total = await self.lectures_repo.get_all_by_lesson_student_id(
            lesson_student_id=lesson_student.id,
            limit=limit,
            offset=offset,
            from_date=from_date,
            to_date=to_date,
            sort_date=sort_date,
            actor=await ObjectPermissionService(self.session_db).actor(user_id),
        )
        
        dtos = [LectureResponseDTO.model_validate(l) for l in lectures]
        
        return PaginationResponseDTO(
            items=dtos,
            total=total,
            limit=limit,
            offset=offset
        )

    async def get_my_lectures(
        self,
        student_user_id: int,
        limit: int = 100,
        offset: int = 0,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        sort_date: str = "desc",
    ) -> PaginationResponseDTO[LectureResponseDTO]:
        student = await self.student_repo.get_student_by_user_id(student_user_id)
        if not student:
            raise PermissionErrorService("Student user not found")
            
        lectures, total = await self.lectures_repo.get_all_by_student_id(
            student_id=student.id,
            limit=limit,
            offset=offset,
            from_date=from_date,
            to_date=to_date,
            sort_date=sort_date,
            actor=await ObjectPermissionService(self.session_db).actor(student_user_id),
        )
        dtos = [LectureResponseDTO.model_validate(l) for l in lectures]
        
        return PaginationResponseDTO(
            items=dtos,
            total=total,
            limit=limit,
            offset=offset
        )

    async def get_lecture_by_id(
        self,
        user_id: int,
        lesson_id: int,
        student_user_id: int,
        lecture_id: int,
    ) -> LectureDTO:
        lesson_student = await ObjectPermissionService(self.session_db).recipient(
            user_id, lesson_id, student_user_id
        )

        lecture = await self.lectures_repo.get_by_id(lecture_id)
        if not lecture or lecture.lesson_student_id != lesson_student.id:
            raise LectureNotFound("Lecture not found")

        actor = await ObjectPermissionService(self.session_db).actor(user_id)
        from src.modules.lectures.models import Lecture
        if not await ObjectPermissionService(self.session_db).repo.material_visible(Lecture, lecture.id, actor):
            raise LectureNotFound()
        dto = LectureDTO.model_validate(lecture)
        dto.pdf_file_path, dto.pdf_file_name, dto.download_mime = await FileAssetsService(self.session_db, self.handler_documents).download(
            lecture.download_asset_id, lecture.pdf_file_path, lecture.pdf_file_name)
        return dto

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

        from src.modules.course_lifecycle.models import FileDeletion
        self.session_db.add_all([FileDeletion(path=p) for p in sorted(
            {lecture.original_file_path, lecture.pdf_file_path} - {None, ''})])
        deleted = await self.lectures_repo.delete_lecture(lecture.id)
        await self.session_db.commit()
        
        return LectureResponseDTO.model_validate(deleted)
