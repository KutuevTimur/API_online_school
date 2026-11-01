from src.modules.files.service import FileAssetsService, discard_uploads
from src.modules.storage.download import safe_display_name
from src.modules.check_permission.service import ObjectPermissionService
from contextlib import asynccontextmanager
from uuid import uuid4
from datetime import datetime, UTC
from pathlib import Path
from typing import AsyncIterator, List, Optional

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.handlers_files.handler_documents import HandlerDocuments
from src.modules.homework_submissions.exception import HomeworkSubmissionNotFound, HomeworkSubmissionNotEditable, SubmissionConflict, EmptySubmission
from src.modules.homework_submissions.models import HomeworkSubmission, HomeworkSubmissionStatus
from src.modules.homework_submissions.models_dto import (
    HomeworkSubmissionResponseDTO,
    ReviewQueueItemDTO,
    HomeworkSubmissionRequestDTO,
    HomeworkSubmissionFileRequestDTO,
    UpdateSubmissionTeacherRequestDTO,
    UpdateSubmissionStudentRequestDTO,
)
from src.modules.homework_submissions.repository import HomeworkSubmissionsRepository
from src.modules.homeworks.repository import HomeworksRepository
from src.modules.path_builder.service import PathBuilder
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository
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
        recipient = await ObjectPermissionService(self.session_db).homework(user_id, homework_id)
        actor = await ObjectPermissionService(self.session_db).actor(user_id)
        if actor.role != user_role:
            raise PermissionErrorService()
        homework = await self.homeworks_repo.get_by_id(homework_id)
        teacher = await self.teacher_repo.get_teacher_by_user_id(user_id) if user_role == UserRole.TEACHER else None
        return homework, recipient.student_id, teacher.id if teacher else None

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
        async with self._mutation() as created_paths:
            await ObjectPermissionService(self.session_db).homework(student_user_id, homework_id, UserRole.STUDENT)
            if not await self.homework_submissions_repo.lock_homework(homework_id):
                raise HomeworkSubmissionNotFound()
            if await self.homework_submissions_repo.working_submission(homework_id):
                raise SubmissionConflict("A working answer already exists; open it instead")
            attempt = await self.homework_submissions_repo.get_max_attempt_number(homework_id) + 1
            submission = await self.homework_submissions_repo.add_submission(HomeworkSubmissionRequestDTO(
                homework_id=homework_id, attempt_number=attempt, text_content=text_content,
                status=HomeworkSubmissionStatus.DRAFT, submitted_at=None))
            await self.session_db.flush()
            await self._append_files(submission.id, files, created_paths, student_user_id)
            result = await self._response(submission.id, student_user_id)
        return result

    @asynccontextmanager
    async def _mutation(self) -> AsyncIterator[list[Path]]:
        created_paths: list[Path] = []
        self.handler_documents.saved_objects.clear()
        self.handler_documents.quota_pending.clear()
        self.handler_documents.transient_objects.clear()
        try:
            yield created_paths
            await self.session_db.commit()
        except BaseException:
            await self.session_db.rollback()
            await discard_uploads(self.session_db, self.handler_documents, list(self.handler_documents.saved_objects) + self.handler_documents.transient_objects)
            raise

    async def _append_files(self, submission_id: int, files: Optional[List[UploadFile]],
                            created_paths: list[Path], uploader_user_id: int, replace_file_id: int | None = None,
                            purpose: str = "answer", recipient_user_id: int | None = None) -> bool:
        from src.modules.handlers_files.exception import InvalidDocumentFormat, FileTooLarge
        incoming = [f for f in files or [] if f.filename]
        count, total = await self.homework_submissions_repo.file_usage(submission_id, replace_file_id, purpose)
        if incoming and count + len(incoming) > 10:
            raise InvalidDocumentFormat("An answer supports at most 10 files")
        data = []
        for file in incoming:
            if not file.filename:
                continue
            name = safe_display_name(file.filename)
            extension = self.handler_documents._validate_extension(file.filename)
            storage_name = uuid4().hex
            original = self.path_builder.get_homework_submission_original(
                homework_submission_id=submission_id, file_name=storage_name, file_type=extension)
            pdf = self.path_builder.get_homework_submission_pdf(
                homework_submission_id=submission_id, file_name=storage_name)
            created_paths.extend([original, pdf])
            original, pdf = await self.handler_documents.save_document(
                document=file, original_dest=original, pdf_dest=pdf)
            total += self.handler_documents.saved_objects[original][0].size
            if total > 100 * 1024 * 1024:
                raise FileTooLarge("Answer source files exceed 100 MiB")
            original_asset_id, download_asset_id = await FileAssetsService(
                self.session_db, self.handler_documents).register(original, pdf, name, uploader_user_id, recipient_user_id)
            data.append(HomeworkSubmissionFileRequestDTO(
                purpose=purpose,
                original_asset_id=original_asset_id, download_asset_id=download_asset_id,
                submission_id=submission_id, source_size=self.handler_documents.saved_objects[original][0].size,
                original_file_path=str(pdf if original_asset_id == download_asset_id else original),
                original_file_name=name, original_file_type=extension,
                pdf_file_path=str(pdf), pdf_file_name=f"{Path(name).stem}{pdf.suffix}"))
        await self.homework_submissions_repo.add_submission_files(data)
        return bool(data)

    async def _response(self, submission_id: int, user_id: int) -> HomeworkSubmissionResponseDTO:
        await self.session_db.flush()
        actor = await ObjectPermissionService(self.session_db).actor(user_id)
        submission = await self.homework_submissions_repo.get_by_submission_id(submission_id, actor=actor, lock=True)
        return await self._public_response(submission)

    async def _public_response(self, submission: HomeworkSubmission) -> HomeworkSubmissionResponseDTO:
        result = HomeworkSubmissionResponseDTO.model_validate(submission)
        from src.modules.files.service import file_descriptors
        descriptors = await file_descriptors(self.session_db, [
            (f.id, f.download_asset_id, f.pdf_file_name or f.original_file_name,
             f"/submissions/{submission.id}/files/{f.id}?homework_id={submission.homework_id}")
            for f in submission.files])
        for file in result.files:
            file.file = descriptors.get(file.id)
        review_ids = {f.id for f in submission.files if f.purpose == "review"}
        result.review_files = [f for f in result.files if f.id in review_ids]
        result.files = [f for f in result.files if f.id not in review_ids]
        result.checked_by = await self.homework_submissions_repo.reviewer_user_id(submission.checked_by)
        return result

    async def review_queue(
        self, teacher_user_id: int, limit: int, offset: int,
        course_id: int | None = None, student_user_id: int | None = None,
    ) -> PaginationResponseDTO[ReviewQueueItemDTO]:
        actor = await ObjectPermissionService(self.session_db).actor(teacher_user_id)
        if actor.role != UserRole.TEACHER:
            raise PermissionErrorService()
        rows, total = await self.homework_submissions_repo.review_queue(
            teacher_user_id, limit, offset, course_id, student_user_id)
        # One descriptor batch for the page; queue must not query files per answer.
        from src.modules.files.service import file_descriptors
        descriptors = await file_descriptors(self.session_db, [
            (file.id, file.download_asset_id, file.pdf_file_name or file.original_file_name,
             f"/submissions/{submission.id}/files/{file.id}?homework_id={submission.homework_id}")
            for submission, *_ in rows for file in submission.files
        ])
        items = []
        for submission, cid, lid, sid, title, first, last, username, course in rows:
            dto = HomeworkSubmissionResponseDTO.model_validate(submission)
            # Submitted answers have no reviewer; never expose an internal teacher id.
            dto.checked_by = None
            for file in dto.files:
                file.file = descriptors.get(file.id)
            items.append(ReviewQueueItemDTO(
                **dto.model_dump(), course_id=cid, lesson_id=lid, student_user_id=sid,
                homework_title=title, student_first_name=first, student_last_name=last,
                student_username=username, course_name=course,
            ))
        return PaginationResponseDTO(items=items, total=total, limit=limit, offset=offset)

    async def _locked(self, user_id: int, role: UserRole, homework_id: int,
                      submission_id: int, expected_version: int | None = None) -> HomeworkSubmission:
        # The same lock order covers create/edit/submit/delete/teacher checking.
        await ObjectPermissionService(self.session_db).homework(user_id, homework_id, role)
        if not await self.homework_submissions_repo.lock_homework(homework_id):
            raise HomeworkSubmissionNotFound()
        actor = await ObjectPermissionService(self.session_db).actor(user_id)
        submission = await self.homework_submissions_repo.get_by_submission_id(submission_id, actor=actor, lock=True)
        if not submission or submission.homework_id != homework_id:
            raise HomeworkSubmissionNotFound()
        if submission.status == HomeworkSubmissionStatus.CHECKED or not submission.is_working:
            raise HomeworkSubmissionNotEditable()
        if expected_version is not None and submission.version != expected_version:
            raise SubmissionConflict("Answer changed; reload the current version")
        return submission

    @staticmethod
    def _has_content(submission: HomeworkSubmission | HomeworkSubmissionResponseDTO) -> bool:
        return bool((submission.text_content or '').strip() or submission.files)

    @staticmethod
    def _touch(submission: HomeworkSubmission) -> None:
        submission.version += 1
        submission.updated_at = datetime.now(UTC)

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
        actor = await ObjectPermissionService(self.session_db).actor(user_id)
        
        submissions, total = await self.homework_submissions_repo.get_submissions_by_homework_id(
            homework_id=homework_id,
            limit=limit,
            offset=offset,
            sort_date=sort_date, actor=actor
        )

        items = [await self._public_response(sub) for sub in submissions]
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
        actor = await ObjectPermissionService(self.session_db).actor(user_id)
        
        submission = await self.homework_submissions_repo.get_by_submission_id(submission_id, actor=actor)
        if not submission or submission.homework_id != homework_id:
            raise HomeworkSubmissionNotFound("Homework submission not found")
            
        return await self._public_response(submission)

    async def update_submission_student(
        self, student_user_id: int, homework_id: int, submission_id: int,
        update_dto: UpdateSubmissionStudentRequestDTO,
        files: Optional[List[UploadFile]] = None, expected_version: int | None = None,
    ) -> HomeworkSubmissionResponseDTO:
        async with self._mutation() as paths:
            submission = await self._locked(student_user_id, UserRole.STUDENT, homework_id,
                                            submission_id, expected_version)
            changed = False
            if 'text_content' in update_dto.model_fields_set and submission.text_content != update_dto.text_content:
                submission.text_content = update_dto.text_content
                changed = True
            changed = await self._append_files(submission_id, files, paths, student_user_id) or changed
            if changed:
                self._touch(submission)
            result = await self._response(submission_id, student_user_id)
            if result.status == HomeworkSubmissionStatus.SUBMITTED and not self._has_content(result):
                raise EmptySubmission("A submitted answer requires text or a file")
        return result

    async def submit_submission(self, student_user_id: int, homework_id: int,
                                submission_id: int) -> HomeworkSubmissionResponseDTO:
        async with self._mutation():
            submission = await self._locked(student_user_id, UserRole.STUDENT, homework_id, submission_id)
            if not self._has_content(submission):
                raise EmptySubmission("Add text or a file before submitting")
            if submission.status == HomeworkSubmissionStatus.DRAFT:
                from src.modules.notifications.service import NotificationsService
                await NotificationsService(self.session_db).homework_event(homework_id, "solution_submitted", submission_id)
                submission.status = HomeworkSubmissionStatus.SUBMITTED
                submission.submitted_at = datetime.now(UTC)
                self._touch(submission)
            result = await self._response(submission_id, student_user_id)
        return result

    async def mutate_file(self, student_user_id: int, homework_id: int, submission_id: int,
                          file_id: int, replacement: UploadFile | None = None,
                          expected_version: int | None = None) -> HomeworkSubmissionResponseDTO:
        async with self._mutation() as paths:
            submission = await self._locked(student_user_id, UserRole.STUDENT, homework_id,
                                            submission_id, expected_version)
            file = next((f for f in submission.files if f.id == file_id), None)
            if file is None:
                raise HomeworkSubmissionNotFound()
            if replacement is not None:
                if not replacement.filename:
                    raise EmptySubmission("Replacement requires a file")
                await self._append_files(submission_id, [replacement], paths, student_user_id, file.id)
            await self.homework_submissions_repo.remove_file(file)
            self._touch(submission)
            result = await self._response(submission_id, student_user_id)
            if result.status == HomeworkSubmissionStatus.SUBMITTED and not self._has_content(result):
                raise EmptySubmission("A submitted answer requires text or a file")
        return result

    async def update_submission_teacher(
        self, teacher_user_id: int, homework_id: int, submission_id: int,
        update_dto: UpdateSubmissionTeacherRequestDTO,
        files: Optional[List[UploadFile]] = None,
    ) -> HomeworkSubmissionResponseDTO:
        async with self._mutation() as created_paths:
            submission = await self._locked(teacher_user_id, UserRole.TEACHER, homework_id, submission_id,
                                            update_dto.expected_version)
            if submission.status != HomeworkSubmissionStatus.SUBMITTED:
                raise SubmissionConflict("Only submitted answers can be reviewed")
            data = update_dto.model_dump(exclude={"expected_version"})
            if data.get('status', HomeworkSubmissionStatus.CHECKED) != HomeworkSubmissionStatus.CHECKED:
                raise SubmissionConflict("A review cannot reopen an answer")
            if files:
                recipient = await ObjectPermissionService(self.session_db).homework(teacher_user_id, homework_id, UserRole.TEACHER)
                student = await self.student_repo.get_student_by_id(recipient.student_id)
                await self._append_files(submission.id, files, created_paths, teacher_user_id,
                                         purpose="review", recipient_user_id=student.user_id)
            teacher = await self.teacher_repo.get_teacher_by_user_id(teacher_user_id)
            for key, value in data.items():
                setattr(submission, key, value)
            from src.modules.notifications.service import NotificationsService
            await NotificationsService(self.session_db).homework_event(homework_id, "solution_checked", submission_id)
            submission.status = HomeworkSubmissionStatus.CHECKED
            submission.checked_at = datetime.now(UTC)
            submission.checked_by = teacher.id
            from src.modules.homework_placements.service import HomeworkPlacementsService
            await HomeworkPlacementsService(self.session_db).freeze(homework_id)
            self._touch(submission)
            result = await self._response(submission_id, teacher_user_id)
        return result

    async def delete_submission(self, user_id: int, user_role: UserRole,
                                homework_id: int, submission_id: int) -> HomeworkSubmissionResponseDTO:
        if user_role not in {UserRole.TEACHER, UserRole.STUDENT}:
            raise PermissionErrorService()
        async with self._mutation():
            submission = await self._locked(user_id, user_role, homework_id, submission_id)
            if await self.homework_submissions_repo.file_count(submission_id) != len(submission.files):
                raise PermissionErrorService("Answer contains read-only history attachments")
            result = await self._public_response(submission)
            for file in list(submission.files):
                await self.homework_submissions_repo.remove_file(file)
            await self.session_db.flush()
            await self.homework_submissions_repo.delete_submission(submission_id)
        return result

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
        actor = await ObjectPermissionService(self.session_db).actor(user_id)
        submission = await self.homework_submissions_repo.get_by_submission_id(submission_id, actor=actor)
        
        if not submission or submission.homework_id != homework_id:
            raise HomeworkSubmissionNotFound("Homework submission not found")

        file_res = await self.homework_submissions_repo.get_submission_file_by_id(file_id)
        if not file_res or file_res.submission_id != submission_id:
            raise HomeworkSubmissionNotFound("Submission file not found")
            
        if file_id not in {f.id for f in submission.files}:
            raise HomeworkSubmissionNotFound()
        from src.modules.homework_submissions.models_dto import HomeworkSubmissionFileDTO
        dto = HomeworkSubmissionFileDTO.model_validate(file_res)
        dto.pdf_file_path, dto.pdf_file_name, dto.download_mime = await FileAssetsService(self.session_db, self.handler_documents).download(
            file_res.download_asset_id, file_res.pdf_file_path or file_res.original_file_path, file_res.pdf_file_name)
        return dto