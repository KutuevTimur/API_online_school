from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.courses.repository import CourseRepository
from src.modules.courses.exception import CourseNotFound, CourseRemovedException
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
        course = await self.course_repo.get_course_by_id(course_id)
        if not course:
            raise CourseNotFound()

        if course.is_deleted:
            raise CourseRemovedException()

        teacher_pk = course.teacher.user_id if course.teacher else None
        if teacher_pk != teacher_user_id:
            raise CourseAccessDeniedException()

        student = await self.student_repo.get_student_by_user_id(data.student_user_id)
        if not student:
            raise StudentNotFound()

        existing = await self.student_courses_repo.get_student_course(
            student_id=student.id,
            course_id=course_id
        )
        if existing:
            raise EnrollmentExistsException()

        dto = CreateStudentCoursesDTO(
            student_id=student.id,
            course_id=course_id,
        )
        enrollment = await self.student_courses_repo.add_student_to_course(dto)
        await self.session_db.commit()
        await self.session_db.refresh(enrollment)
        
        return StudentCourseResponseDTO.model_validate(enrollment)

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
        course = await self.course_repo.get_course_by_id(course_id)
        if not course:
            raise CourseNotFound()

        teacher_pk = course.teacher.user_id if course.teacher else None
        if teacher_pk != teacher_user_id:
            raise CourseAccessDeniedException()

        student = await self.student_repo.get_student_by_user_id(student_user_id)
        if not student:
            raise StudentNotFound()

        existing = await self.student_courses_repo.get_student_course(
            student_id=student.id,
            course_id=course_id
        )
        if not existing:
            raise EnrollmentNotFoundException()

        await self.student_courses_repo.remove_student_from_course(
            student_id=student.id,
            course_id=course_id
        )
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
