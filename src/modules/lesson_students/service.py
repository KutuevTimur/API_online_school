from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from asyncpg.exceptions import UniqueViolationError

from src.modules.check_permission.exception import PermissionErrorService
from src.modules.lesson_students.exception import LessonStudentAlreadyExists, LessonStudentNotFound
from src.modules.lesson_students.models_dto import CreateLessonStudentRequestDTO, LessonStudentResponseDTO
from src.modules.lesson_students.repository import LessonStudentsRepository
from src.modules.lessons.exception import LessonNotFound
from src.modules.lessons.repository import LessonsRepository
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository


class LessonStudentsService:
    def __init__(
        self,
        lesson_students_repo: LessonStudentsRepository,
        lessons_repo: LessonsRepository,
        student_repo: StudentRepository,
        teacher_repo: TeacherRepository,
        session_db: AsyncSession,
    ):
        self.lesson_students_repo = lesson_students_repo
        self.lessons_repo = lessons_repo
        self.student_repo = student_repo
        self.teacher_repo = teacher_repo
        self.session_db = session_db

    async def add_student(
        self,
        teacher_user_id: int,
        data: CreateLessonStudentRequestDTO,
    ) -> LessonStudentResponseDTO:
        # Проверяем, что урок принадлежит учителю
        teacher = await self.teacher_repo.get_teacher_by_user_id(teacher_user_id)
        if not teacher:
            raise PermissionErrorService("Teacher user not found")

        lesson = await self.lessons_repo.get_lesson_by_id(data.lesson_id)
        if not lesson:
            raise LessonNotFound()
        
        if lesson.teacher_id != teacher.id:
            raise PermissionErrorService("You do not have permission to modify this lesson")

        # Получаем student_id по student_user_id
        student = await self.student_repo.get_student_by_user_id(data.student_user_id)
        if not student:
            raise PermissionErrorService("Student user not found")

        # Проверяем уникальность
        existing = await self.lesson_students_repo.get_by_lesson_and_student(
            lesson_id=data.lesson_id, 
            student_id=student.id
        )
        if existing:
            raise LessonStudentAlreadyExists()

        try:
            lesson_student = await self.lesson_students_repo.add_student_to_lesson(
                data=data,
            )
            await self.session_db.commit()
            await self.session_db.refresh(lesson_student)
            return LessonStudentResponseDTO.model_validate(lesson_student)
        except IntegrityError as e:
            await self.session_db.rollback()
            if "uq_lesson_student" in str(e) or (e.orig and hasattr(e.orig, "__cause__") and isinstance(e.orig.__cause__, UniqueViolationError)):
                raise LessonStudentAlreadyExists()
            raise

    async def remove_student(
        self,
        teacher_user_id: int,
        lesson_id: int,
        student_user_id: int,
    ) -> LessonStudentResponseDTO:
        teacher = await self.teacher_repo.get_teacher_by_user_id(teacher_user_id)
        if not teacher:
            raise PermissionErrorService("Teacher user not found")

        # Проверяем, что урок принадлежит учителю
        lesson = await self.lessons_repo.get_lesson_by_id(lesson_id)
        if not lesson:
            raise LessonNotFound()
        
        if lesson.teacher_id != teacher.id:
            raise PermissionErrorService("You do not have permission to modify this lesson")

        # Находим студента
        student = await self.student_repo.get_student_by_user_id(student_user_id)
        if not student:
            raise LessonStudentNotFound("Student user not found")

        deleted = await self.lesson_students_repo.delete_student_from_lesson(
            lesson_id=lesson_id, 
            student_id=student.id
        )
        if not deleted:
            raise LessonStudentNotFound()

        await self.session_db.commit()
        return LessonStudentResponseDTO.model_validate(deleted)
