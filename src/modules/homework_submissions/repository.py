from src.modules.check_permission.repository import submission_scope
from sqlalchemy.orm import with_loader_criteria
from typing import List, Tuple, Optional
from datetime import datetime

from sqlalchemy import select, update, delete, func, desc, asc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.repository_model import BaseRepository
from src.modules.homework_submissions.models import HomeworkSubmission, HomeworkSubmissionFile
from src.modules.homeworks.models import Homework
from src.modules.homework_submissions.models_dto import HomeworkSubmissionRequestDTO, HomeworkSubmissionFileRequestDTO


class HomeworkSubmissionsRepository(BaseRepository):
    def __init__(self, session: AsyncSession):
        super().__init__(
            session=session,
            model=HomeworkSubmission,
        )

    async def add_submission(self, data: HomeworkSubmissionRequestDTO) -> HomeworkSubmission:
        return self.add(data)

    async def add_submission_files(self, files_data: List[HomeworkSubmissionFileRequestDTO]) -> None:
        if not files_data:
            return
        files = [HomeworkSubmissionFile(**file.model_dump()) for file in files_data]
        self.session.add_all(files)

    async def get_by_submission_id(self, submission_id: int, actor=None, lock: bool = False) -> HomeworkSubmission | None:
        stmt = (
            select(HomeworkSubmission)
            .where(HomeworkSubmission.id == submission_id)
            .options(selectinload(HomeworkSubmission.files))
        )
        if lock:
            stmt = stmt.with_for_update().execution_options(populate_existing=True)
        if actor is not None:
            file_predicate = submission_scope(HomeworkSubmissionFile, actor.id, actor.role)
            stmt = stmt.where(submission_scope(HomeworkSubmission, actor.id, actor.role)).options(
                with_loader_criteria(HomeworkSubmissionFile, file_predicate)).execution_options(populate_existing=True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_homework_and_attempt(self, homework_id: int, attempt_number: int) -> HomeworkSubmission | None:
        stmt = (
            select(HomeworkSubmission)
            .where(HomeworkSubmission.homework_id == homework_id)
            .where(HomeworkSubmission.attempt_number == attempt_number)
            .options(selectinload(HomeworkSubmission.files))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_max_attempt_number(self, homework_id: int) -> int:
        stmt = select(func.max(HomeworkSubmission.attempt_number)).where(HomeworkSubmission.homework_id == homework_id)
        result = await self.session.scalar(stmt)
        return result or 0

    async def get_submissions_by_homework_id(
        self,
        homework_id: int,
        limit: int = 100,
        offset: int = 0,
        sort_date: str = "desc",
        actor=None,
    ) -> Tuple[List[HomeworkSubmission], int]:
        scope = submission_scope(HomeworkSubmission, actor.id, actor.role) if actor else True
        total = await self.session.scalar(select(func.count()).select_from(HomeworkSubmission).where(
            HomeworkSubmission.homework_id == homework_id, scope)) or 0
        count_over = func.count().over().label('total_count')
        
        stmt = select(HomeworkSubmission, count_over).where(
            HomeworkSubmission.homework_id == homework_id, scope
        )

        if sort_date.lower() == "asc":
            stmt = stmt.order_by(HomeworkSubmission.created_at.asc())
        else:
            stmt = stmt.order_by(HomeworkSubmission.created_at.desc())
            
        stmt = stmt.limit(limit).offset(offset)
        stmt = stmt.options(selectinload(HomeworkSubmission.files))

        if actor is not None:
            file_predicate = submission_scope(HomeworkSubmissionFile, actor.id, actor.role)
            stmt = stmt.where(submission_scope(HomeworkSubmission, actor.id, actor.role)).options(
                with_loader_criteria(HomeworkSubmissionFile, file_predicate)).execution_options(populate_existing=True)
        result = await self.session.execute(stmt)
        rows = result.all()

        if not rows:
            return [], total
            
        submissions = [row[0] for row in rows]
        
        return submissions, total

    async def update_submission(self, submission_id: int, values: dict) -> HomeworkSubmission:
        stmt = (
            update(HomeworkSubmission)
            .where(HomeworkSubmission.id == submission_id)
            .values(**values)
            .returning(HomeworkSubmission)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()

    async def delete_submission(self, submission_id: int) -> HomeworkSubmission | None:
        stmt = (
            delete(HomeworkSubmission)
            .where(HomeworkSubmission.id == submission_id)
            .returning(HomeworkSubmission)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_submission_files(self, submission_id: int) -> List[HomeworkSubmissionFile]:
        stmt = (
            delete(HomeworkSubmissionFile)
            .where(HomeworkSubmissionFile.submission_id == submission_id)
            .returning(HomeworkSubmissionFile)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_submission_file_by_id(self, file_id: int) -> HomeworkSubmissionFile | None:
        stmt = (
            select(HomeworkSubmissionFile)
            .where(HomeworkSubmissionFile.id == file_id)
            .options(
                selectinload(HomeworkSubmissionFile.submission)
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def lock_homework(self, homework_id: int) -> Homework | None:
        return await self.session.scalar(select(Homework).where(Homework.id == homework_id)
                                         .with_for_update().execution_options(populate_existing=True))

    async def working_submission(self, homework_id: int) -> HomeworkSubmission | None:
        return await self.session.scalar(select(HomeworkSubmission).where(
            HomeworkSubmission.homework_id == homework_id, HomeworkSubmission.is_working.is_(True)))

    async def remove_file(self, file: HomeworkSubmissionFile) -> None:
        from src.modules.course_lifecycle.models import FileDeletion
        paths = {file.original_file_path, file.pdf_file_path} - {None}
        self.session.add_all([FileDeletion(path=p) for p in sorted(paths)])
        await self.session.delete(file)
        await self.session.flush()
        from src.modules.files.repository import FileAssetsRepository
        await FileAssetsRepository(self.session).prune({file.original_asset_id, file.download_asset_id} - {None})

    async def file_usage(self, submission_id: int, exclude_file_id: int | None = None, purpose: str = "answer") -> tuple[int, int]:
        from src.modules.files.models import FileAsset
        stmt = select(func.count(HomeworkSubmissionFile.id),
                      func.coalesce(func.sum(func.coalesce(HomeworkSubmissionFile.source_size, FileAsset.size, 20 * 1024 * 1024)), 0)).select_from(
                          HomeworkSubmissionFile).outerjoin(FileAsset, FileAsset.id == HomeworkSubmissionFile.original_asset_id).where(
                              HomeworkSubmissionFile.submission_id == submission_id, HomeworkSubmissionFile.purpose == purpose)
        if exclude_file_id is not None:
            stmt = stmt.where(HomeworkSubmissionFile.id != exclude_file_id)
        row = (await self.session.execute(stmt)).one()
        return int(row[0]), int(row[1])

    async def file_count(self, submission_id: int) -> int:
        return await self.session.scalar(select(func.count()).select_from(HomeworkSubmissionFile).where(
            HomeworkSubmissionFile.submission_id == submission_id)) or 0

    async def reviewer_user_id(self, teacher_id: int | None) -> int | None:
        from src.modules.teachers.models import Teacher
        if teacher_id is None:
            return None
        return await self.session.scalar(select(Teacher.user_id).where(Teacher.id == teacher_id))

    async def review_queue(
        self, teacher_user_id: int, limit: int, offset: int,
        course_id: int | None = None, student_user_id: int | None = None,
    ) -> tuple[list[tuple[HomeworkSubmission, int, int, int, str, str, str, str, str]], int]:
        from sqlalchemy import exists, or_, true
        from src.modules.homework_submissions.models import HomeworkSubmissionStatus
        from src.modules.homeworks.models import Homework
        from src.modules.lesson_students.models import LessonStudent
        from src.modules.lessons.models import Lesson
        from src.modules.courses.models import Course
        from src.modules.students.models import Student
        from src.modules.teachers.models import Teacher
        from src.modules.student_courses.models import StudentCourse
        from src.modules.teacher_students.models import TeacherStudent

        from src.modules.users.models import User

        stmt = (select(HomeworkSubmission, Course.id.label("queue_course_id"),
                       Lesson.id.label("queue_lesson_id"), Student.user_id.label("queue_student_user_id"),
                       Homework.title.label("queue_homework_title"),
                       Student.first_name.label("queue_first_name"), Student.last_name.label("queue_last_name"),
                       User.username.label("queue_username"), Course.name.label("queue_course_name"))
            .join(Homework, Homework.id == HomeworkSubmission.homework_id)
            .join(LessonStudent, LessonStudent.id == Homework.lesson_student_id)
            .join(Lesson, Lesson.id == LessonStudent.lesson_id)
            .join(Course, Course.id == Lesson.course_id)
            .join(Teacher, Teacher.id == Course.teacher_id)
            .join(Student, Student.id == LessonStudent.student_id)
            .join(User, User.id == Student.user_id)
            .join(StudentCourse, (StudentCourse.course_id == Course.id) &
                  (StudentCourse.student_id == Student.id))
            .where(Teacher.user_id == teacher_user_id, Lesson.teacher_id == Teacher.id,
                HomeworkSubmission.status == HomeworkSubmissionStatus.SUBMITTED,
                HomeworkSubmission.is_working.is_(True),
                Course.is_deleted.is_(False), Lesson.is_deleted.is_(False),
                LessonStudent.access_ended_at.is_(None), StudentCourse.is_deleted.is_(False),
                StudentCourse.history_revoked.is_(False), StudentCourse.access_ended_at.is_(None),
                or_(StudentCourse.expires_at.is_(None), StudentCourse.expires_at > func.now()),
                ~exists(select(TeacherStudent.id).where(
                    TeacherStudent.teacher_id == Teacher.id, TeacherStudent.student_id == Student.id,
                    TeacherStudent.ended_at.is_not(None)).correlate(Teacher, Student))))
        if course_id is not None:
            stmt = stmt.where(Course.id == course_id)
        if student_user_id is not None:
            stmt = stmt.where(Student.user_id == student_user_id)
        # Count and page share a single statement snapshot, including an empty offset page.
        filtered = stmt.subquery()
        page = (stmt.order_by(HomeworkSubmission.submitted_at.asc().nulls_last(), HomeworkSubmission.id)
                .limit(limit).offset(offset).subquery())
        from sqlalchemy.orm import aliased
        submission = aliased(HomeworkSubmission, page)
        count = select(func.count()).select_from(filtered).subquery()
        result = await self.session.execute(select(
            submission, page.c.queue_course_id, page.c.queue_lesson_id,
            page.c.queue_student_user_id, page.c.queue_homework_title,
            page.c.queue_first_name, page.c.queue_last_name, page.c.queue_username,
            page.c.queue_course_name, count.c[0]
        ).select_from(count.outerjoin(page, true())).options(selectinload(submission.files))
         .order_by(submission.submitted_at.asc().nulls_last(), submission.id)
         .execution_options(populate_existing=True))
        rows = result.all()
        return [tuple(row[:9]) for row in rows if row[0] is not None], rows[0][-1]
