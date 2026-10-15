from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.base.repository_model import BaseRepository
from src.modules.courses.models import Course
from src.modules.lessons.models import Lesson
from src.modules.lesson_students.models import LessonStudent
from src.modules.student_courses.models import StudentCourse
from src.modules.lectures.models import Lecture
from src.modules.homeworks.models import Homework
from src.modules.homework_submissions.models import HomeworkSubmission, HomeworkSubmissionFile
from src.modules.course_lifecycle.models import EnrollmentGap, LifecycleAudit, FileDeletion
from src.modules.students.models import Student
from src.modules.teachers.models import Teacher


FILE_COLUMNS = [(Course, 'avatar_path'), (Student, 'avatar_path'), (Teacher, 'avatar_path')]
for entity in (Lecture, Homework, HomeworkSubmissionFile):
    FILE_COLUMNS.extend([(entity, 'original_file_path'), (entity, 'pdf_file_path')])


class LifecycleRepository(BaseRepository):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, model=Course)

    async def course(self, course_id: int) -> Course | None:
        return await self.session.scalar(select(Course).where(Course.id == course_id)
                                         .with_for_update().execution_options(populate_existing=True))

    async def lesson_course_id(self, lesson_id: int) -> int | None:
        return await self.session.scalar(select(Lesson.course_id).where(Lesson.id == lesson_id))

    async def lesson(self, lesson_id: int) -> Lesson | None:
        return await self.session.scalar(select(Lesson).where(Lesson.id == lesson_id)
                                         .with_for_update().execution_options(populate_existing=True))

    async def enrollment(self, course_id: int, user_id: int) -> StudentCourse | None:
        return await self.session.scalar(select(StudentCourse).join(Student).where(
            StudentCourse.course_id == course_id, Student.user_id == user_id).with_for_update(of=StudentCourse))

    async def purge(self, course_id: int) -> None:
        lessons = select(Lesson.id).where(Lesson.course_id == course_id)
        recipients = select(LessonStudent.id).where(LessonStudent.lesson_id.in_(lessons))
        homeworks = select(Homework.id).where(Homework.lesson_student_id.in_(recipients))
        submissions = select(HomeworkSubmission.id).where(HomeworkSubmission.homework_id.in_(homeworks))
        filters = {
            Course: Course.id == course_id,
            Lecture: Lecture.lesson_student_id.in_(recipients),
            Homework: Homework.lesson_student_id.in_(recipients),
            HomeworkSubmissionFile: HomeworkSubmissionFile.submission_id.in_(submissions),
        }
        paths = set()
        for model, name in FILE_COLUMNS:
            if model in filters:
                paths.update(p for p in (await self.session.scalars(
                    select(getattr(model, name)).where(filters[model]))).all() if p)
        self.session.add_all([FileDeletion(path=p) for p in sorted(paths)])
        for model, predicate in [
            (HomeworkSubmissionFile, filters[HomeworkSubmissionFile]),
            (HomeworkSubmission, HomeworkSubmission.id.in_(submissions)),
            (Homework, filters[Homework]), (Lecture, filters[Lecture]),
            (LessonStudent, LessonStudent.id.in_(recipients)), (Lesson, Lesson.id.in_(lessons)),
            (EnrollmentGap, EnrollmentGap.enrollment_id.in_(select(StudentCourse.id).where(StudentCourse.course_id == course_id))),
            (StudentCourse, StudentCourse.course_id == course_id), (Course, Course.id == course_id),
        ]:
            await self.session.execute(delete(model).where(predicate).execution_options(synchronize_session=False))

    async def referenced_paths(self) -> set[str]:
        paths = set()
        for model, name in FILE_COLUMNS:
            paths.update(p for p in (await self.session.scalars(select(getattr(model, name)))).all() if p)
        return paths

    async def pending(self, limit: int) -> list[FileDeletion]:
        return list((await self.session.scalars(select(FileDeletion).where(
            FileDeletion.completed.is_(False)).order_by(FileDeletion.attempts, FileDeletion.id)
            .limit(limit).with_for_update(skip_locked=True))).all())
