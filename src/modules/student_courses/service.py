from typing import List, Tuple, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.courses.repository import CourseRepository
from src.modules.courses.exception import CourseNotFound, CourseRemovedException
from src.modules.student_courses.models import StudentCourse
from src.modules.students.models import Student
from src.modules.students.repository import StudentRepository
from src.modules.students.exception import StudentNotFound
from src.modules.student_courses.repository import StudentCoursesRepository
from src.modules.student_courses.models_dto import (
    CreateStudentCoursesDTO,
    StudentCourseResponseDTO,
    EnrollStudentRequestDTO
)
from src.modules.student_courses.exception import (
    EnrollmentExistsException,
    EnrollmentNotFoundException,
    CourseAccessDeniedException
)


class StudentCoursesService:
    def __init__(
        self,
        student_courses_repo: StudentCoursesRepository,
        course_repo: CourseRepository,
        student_repo: StudentRepository,
        session_db: AsyncSession,
    ):
        self.student_courses_repo = student_courses_repo
        self.course_repo = course_repo
        self.student_repo = student_repo
        self.session_db = session_db

    async def cheek_student_course(
        self,
        course_id: int,
        student_user_id: int,
        teacher_user_id: Optional[int] = None,
        deletion_check: Optional[bool] = False,
    ) -> Tuple[StudentCourse | None, Student]:
        """
        Проверяет наличие всех связанных сущностей БД, проверяет, что курс не удалён.
        :param teacher_user_id: Если передать, то проверит, что данный учитель является владельцем курса
        :raises CourseNotFound:
        :raises CourseRemovedException:
        :raises CourseAccessDeniedException:
        :raises StudentNotFound:
        :raises EnrollmentNotFoundException: если стоит флаг deletion_check и курс не найден или удалён
        """
        course = await self.course_repo.get_course_by_id(course_id)
        if not course:
            raise CourseNotFound()

        if course.is_deleted:
            raise CourseRemovedException()

        if teacher_user_id:
            teacher_pk = course.teacher.user_id if course.teacher else None
            if teacher_pk != teacher_user_id:
                raise CourseAccessDeniedException()

        student = await self.student_repo.get_student_by_user_id(student_user_id)
        if not student:
            raise StudentNotFound()

        student_course = await self.student_courses_repo.get_student_course(
            student_id=student.id,
            course_id=course_id
        )

        if deletion_check and (not student_course or student_course.is_deleted):
            raise EnrollmentNotFoundException()

        return student_course, student

    async def enroll_student(
        self,
        teacher_user_id: int,
        course_id: int,
        data: EnrollStudentRequestDTO,
    ) -> StudentCourseResponseDTO:
        """
        Прикрепить студента к курсу.
        :raises CourseNotFound:
        :raises CourseRemovedException:
        :raises CourseAccessDeniedException:
        :raises StudentNotFound:
        :raises EnrollmentExistsException:
        """
        existing, student = await self.cheek_student_course(
            course_id=course_id,
            student_user_id=data.student_user_id,
            teacher_user_id=teacher_user_id,
        )

        if existing:
            if not existing.is_deleted:
                raise EnrollmentExistsException()
            else:
                existing.restore()
                await self.session_db.commit()
                await self.session_db.refresh(existing)
                return StudentCourseResponseDTO.model_validate(existing)

        dto = CreateStudentCoursesDTO(
            student_id=student.id,
            course_id=course_id,
        )
        enrollment = await self.student_courses_repo.add_student_to_course(dto)
        await self.session_db.commit()
        await self.session_db.refresh(enrollment)
        
        return StudentCourseResponseDTO.model_validate(enrollment)

    async def unenroll_student_from_student(
        self,
        course_id: int,
        student_user_id: int,
    ) -> None:
        """
        Открепить студента от курса. Необходим для ручки ученика
        :raises CourseNotFound:
        :raises CourseAccessDeniedException:
        :raises StudentNotFound:
        :raises EnrollmentNotFoundException:
        """
        existing, student = await self.cheek_student_course(
            course_id=course_id,
            student_user_id=student_user_id,
            deletion_check=True,
        )

        existing.soft_delete()
        await self.session_db.commit()

    async def unenroll_student(
        self,
        teacher_user_id: int,
        course_id: int,
        student_user_id: int,
    ) -> None:
        """
        Открепить студента от курса
        :raises CourseNotFound:
        :raises CourseAccessDeniedException:
        :raises StudentNotFound:
        :raises EnrollmentNotFoundException:
        """

        existing, student = await self.cheek_student_course(
            course_id=course_id,
            student_user_id=student_user_id,
            teacher_user_id=teacher_user_id,
            deletion_check=True,
        )

        existing.soft_delete()
        await self.session_db.commit()

    async def get_students_for_course(
        self,
        teacher_user_id: int,
        course_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[int, List[StudentCourseResponseDTO]]:
        """
        Открепить студента от курса
        :raises CourseNotFound:
        :raises CourseAccessDeniedException:
        """
        course = await self.course_repo.get_course_by_id(course_id)
        if not course:
            raise CourseNotFound()
            
        teacher_pk = course.teacher.user_id if course.teacher else None
        if teacher_pk != teacher_user_id:
            raise CourseAccessDeniedException()

        total, records = await self.student_courses_repo.get_students_for_course(
            course_id=course_id,
            limit=limit,
            offset=offset
        )
        
        results = [StudentCourseResponseDTO.model_validate(r) for r in records]
        return total, results
