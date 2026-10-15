from src.modules.files.service import FileAssetsService, atomic_file_upload
from src.modules.check_permission.service import ObjectPermissionService
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
from src.modules.homeworks.models import Homework
from src.modules.lesson_students.repository import LessonStudentsRepository
from src.modules.lessons.repository import LessonsRepository
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository
from src.modules.path_builder.service import PathBuilder
from src.modules.storage.download import safe_display_name


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
        return await ObjectPermissionService(self.session_db).recipient(
            teacher_user_id, lesson_id, student_user_id, write=True
        )

    @atomic_file_upload
    async def create_homework(
        self,
        teacher_user_id: int,
        lesson_id: int,
        student_user_id: int,
        title: str,
        description: Optional[str] = None,
        file: Optional[UploadFile] = None,
    ) -> HomeworkResponseDTO:
        lesson_student = await self._get_and_check_lesson_student(
            teacher_user_id=teacher_user_id,
            lesson_id=lesson_id,
            student_user_id=student_user_id,
        )

        has_file = file is not None and file.filename != ""
        file_name = Path(safe_display_name(file.filename)).stem if has_file else None
        file_type = self.handler_documents._validate_extension(file.filename) if has_file else None

        dto = CreateHomeworkRequestDTO(
            lesson_student_id=lesson_student.id,
            title=title,
            description=description,
            deadline=None,
            original_file_path="",
            original_file_name=f"{file_name}.{file_type}" if file_name else None,
            original_file_type=file_type,
            pdf_file_path="",
            pdf_file_name=f"{file_name}.pdf" if file_name else None,
        )

        if not has_file:
            dto.original_file_path = None
            dto.pdf_file_path = None

        storage_name = uuid.uuid4().hex
        homework = await self.homeworks_repo.add_homework(dto)
        await self.session_db.flush()
        from src.modules.homework_placements.service import HomeworkPlacementsService
        await HomeworkPlacementsService(self.session_db).original(homework)

        if has_file:
            original_dest = self.path_builder.get_homework_original(
                homework_id=homework.id,
                file_name=storage_name,
                file_type=file_type,
            )
            pdf_dest = self.path_builder.get_homework_pdf(
                homework_id=homework.id,
                file_name=storage_name,
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

        if has_file:
            homework.original_asset_id, homework.download_asset_id = await FileAssetsService(
                self.session_db, self.handler_documents).register(original_path, pdf_path, dto.original_file_name, teacher_user_id, student_user_id)
            homework.pdf_file_name = Path(dto.original_file_name).stem + pdf_path.suffix
            if homework.original_asset_id == homework.download_asset_id:
                homework.original_file_path = str(pdf_path)

        await self.session_db.commit()
        self.handler_documents.upload_committed = True
        await self.session_db.refresh(homework)
        
        return await self._placement_response(homework, teacher_user_id)

    async def get_homeworks(
        self,
        user_id: int,
        lesson_id: int,
        student_user_id: int,
    ) -> List[HomeworkResponseDTO]:
        lesson_student = await ObjectPermissionService(self.session_db).recipient(
            user_id, lesson_id, student_user_id
        )

        from src.modules.homework_placements.repository import HomeworkPlacementsRepository
        actor = await ObjectPermissionService(self.session_db).actor(user_id)
        homeworks = await HomeworkPlacementsRepository(self.session_db).lesson_homeworks(lesson_student.id, actor)
        return [await self._placement_response(h, user_id, lesson_student.id) for h in homeworks]

    async def get_my_homeworks(self, student_user_id: int) -> List[HomeworkResponseDTO]:
        student = await self.student_repo.get_student_by_user_id(student_user_id)
        if not student:
            raise PermissionErrorService("Student user not found")
            
        homeworks = await self.homeworks_repo.get_all_by_student_id(student.id, actor=await ObjectPermissionService(self.session_db).actor(student_user_id))
        return [await self._placement_response(h, student_user_id) for h in homeworks]

    async def get_homework_file(
        self,
        user_id: int,
        lesson_id: int,
        student_user_id: int,
        homework_id: int,
    ) -> HomeworkDTO:
        lesson_student = await ObjectPermissionService(self.session_db).recipient(
            user_id, lesson_id, student_user_id
        )

        homework = await self.homeworks_repo.get_by_id(homework_id)
        if not homework:
            raise HomeworkNotFound("Homework not found")
        from src.modules.homework_placements.repository import HomeworkPlacementsRepository
        actor = await ObjectPermissionService(self.session_db).actor(user_id)
        visible = await HomeworkPlacementsRepository(self.session_db).placements(homework_id, actor)
        if not any(p.lesson_student_id == lesson_student.id for p in visible):
            raise HomeworkNotFound("Homework not found")
            
        await ObjectPermissionService(self.session_db).homework(user_id, homework_id)
        if not homework.pdf_file_path:
            raise HomeworkNotFound("No files attached to this homework")

        dto = HomeworkDTO.model_validate(homework)
        dto.pdf_file_path, dto.pdf_file_name, dto.download_mime = await FileAssetsService(self.session_db, self.handler_documents).download(
            homework.download_asset_id, homework.pdf_file_path, homework.pdf_file_name)
        return dto

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

        from src.modules.homework_placements.repository import HomeworkPlacementsRepository
        from src.modules.homework_submissions.exception import HomeworkSubmissionNotEditable
        repo = HomeworkPlacementsRepository(self.session_db)
        homework = await repo.homework(homework.id)
        if homework.deadline_frozen_at is not None or await repo.checked(homework.id):
            raise HomeworkSubmissionNotEditable()
        from src.modules.course_lifecycle.models import FileDeletion
        self.session_db.add_all([FileDeletion(path=p) for p in sorted(
            {homework.original_file_path, homework.pdf_file_path} - {None, ''})])
        deleted = await self.homeworks_repo.delete_homework(homework.id)
        await self.session_db.commit()
        
        return HomeworkResponseDTO.model_validate(deleted)

    async def _placement_response(self, homework: Homework, user_id: int, recipient_id: int | None = None) -> HomeworkResponseDTO:
        from src.modules.homework_placements.service import HomeworkPlacementsService
        service = HomeworkPlacementsService(self.session_db)
        actor = await ObjectPermissionService(self.session_db).actor(user_id)
        placements = await service.repo.placements(homework.id, actor)
        if recipient_id is not None:
            placements = [p for p in placements if p.lesson_student_id == recipient_id]
        dto = HomeworkResponseDTO.model_validate(homework)
        dto.submission_status = await service.repo.working_status(homework.id, actor)
        if dto.submission_status != "checked":
            dto.deadline_frozen_at = None
        if placements:
            p = await service.response(placements[-1], actor, dto.submission_status == "checked")
            dto.deadline = p.due_at
            dto.placement_id, dto.placement_kind, dto.placement_lesson_id = p.id, p.kind, p.lesson_id
            dto.due_lesson_id = p.due_lesson_id
        else:
            dto.deadline = None
        return dto
