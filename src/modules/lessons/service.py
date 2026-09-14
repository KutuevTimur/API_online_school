from typing import Tuple, List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.lessons.repository import LessonsRepository
from src.modules.lessons.models_dto import (
    LessonResponseDTO, 
    CreateLessonRequestDTO, 
    CreateLessonDTO, 
    UpdateLessonRequestDTO
)
from src.modules.lessons.exception import LessonNotFound
from src.modules.courses.repository import CourseRepository
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository
from src.modules.users.models_dto import UserDTO
from src.modules.users.models import UserRole
from src.modules.check_permission.exception import PermissionErrorService


class LessonsService:
    def __init__(
        self,
        lessons_repo: LessonsRepository,
        course_repo: CourseRepository,
        student_repo: StudentRepository,
        teacher_repo: TeacherRepository,
        session_db: AsyncSession,
    ):
        self.lessons_repo = lessons_repo
        self.course_repo = course_repo
        self.student_repo = student_repo
        self.teacher_repo = teacher_repo
        self.session_db = session_db

    async def get_lessons(
        self,
        current_user: UserDTO,
        limit: int,
        offset: int,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        course_id: Optional[int] = None,
    ) -> PaginationResponseDTO[LessonResponseDTO]:
        
        teacher_id = None
        student_id = None
        
        if current_user.role == UserRole.TEACHER:
            teacher = await self.teacher_repo.get_teacher_by_user_id(current_user.id)
            if teacher:
                teacher_id = teacher.id
        elif current_user.role == UserRole.STUDENT:
            student = await self.student_repo.get_student_by_user_id(current_user.id)
            if student:
                student_id = student.id

        lessons, total = await self.lessons_repo.get_lessons(
            limit=limit,
            offset=offset,
            from_date=from_date,
            to_date=to_date,
            course_id=course_id,
            teacher_id=teacher_id,
            student_id=student_id,
        )

        dtos = []
        for lesson in lessons:
            dto = LessonResponseDTO.model_validate(lesson)
            
            has_lecture = False
            has_homework = False
            
            for ls in lesson.lesson_students:
                if student_id and ls.student_id != student_id:
                    continue
                
                if ls.lectures:
                    has_lecture = True
                if ls.homeworks:
                    has_homework = True
                    
            dto.has_lecture = has_lecture
            dto.has_homework = has_homework
            dtos.append(dto)

        return PaginationResponseDTO(
            items=dtos,
            total=total,
            limit=limit,
            offset=offset
        )

    async def get_lesson(self, current_user: UserDTO, lesson_id: int) -> LessonResponseDTO:
        lesson = await self.lessons_repo.get_lesson_by_id(lesson_id)
        if not lesson:
            raise LessonNotFound("Lesson not found")

        student_id = None
        if current_user.role == UserRole.TEACHER:
            teacher = await self.teacher_repo.get_teacher_by_user_id(current_user.id)
            if not teacher or lesson.teacher_id != teacher.id:
                raise PermissionErrorService("Access denied")
        elif current_user.role == UserRole.STUDENT:
            student = await self.student_repo.get_student_by_user_id(current_user.id)
            if not student:
                raise PermissionErrorService("Access denied")
            student_id = student.id
            
            is_enrolled = any(ls.student_id == student_id for ls in lesson.lesson_students)
            if not is_enrolled:
                raise PermissionErrorService("You are not enrolled in this lesson")

        dto = LessonResponseDTO.model_validate(lesson)
        has_lecture = False
        has_homework = False
        
        for ls in lesson.lesson_students:
            if student_id and ls.student_id != student_id:
                continue
            if ls.lectures:
                has_lecture = True
            if ls.homeworks:
                has_homework = True
                
        dto.has_lecture = has_lecture
        dto.has_homework = has_homework
        return dto

    async def create_lesson(self, teacher_user_id: int, data: CreateLessonRequestDTO) -> LessonResponseDTO:
        teacher = await self.teacher_repo.get_teacher_by_user_id(teacher_user_id)
        if not teacher:
            raise PermissionErrorService("Teacher not found")

        course = await self.course_repo.get_course_by_id(data.course_id)
        if not course:
            raise PermissionErrorService("Course not found")

        # Проверка, что курс принадлежит именно этому учителю
        if course.teacher_id != teacher.id:
            raise PermissionErrorService("Course does not belong to you")

        create_dto = CreateLessonDTO(
            course_id=data.course_id,
            teacher_id=teacher.id,
            title=data.title,
            topic=data.topic,
            description=data.description,
            scheduled_at=data.scheduled_at,
            duration_minutes=data.duration_minutes
        )

        lesson = await self.lessons_repo.add_lesson(create_dto)
        await self.session_db.commit()
        await self.session_db.refresh(lesson)

        return LessonResponseDTO.model_validate(lesson)

    async def update_lesson(self, teacher_user_id: int, lesson_id: int, data: UpdateLessonRequestDTO) -> LessonResponseDTO:
        teacher = await self.teacher_repo.get_teacher_by_user_id(teacher_user_id)
        if not teacher:
            raise PermissionErrorService("Teacher not found")

        lesson = await self.lessons_repo.get_lesson_by_id(lesson_id)
        if not lesson:
            raise LessonNotFound("Lesson not found")

        if lesson.teacher_id != teacher.id:
            raise PermissionErrorService("Access denied to update this lesson")

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            return LessonResponseDTO.model_validate(lesson)

        updated_lesson = await self.lessons_repo.update_lesson(lesson_id, update_data)
        await self.session_db.commit()
        
        return LessonResponseDTO.model_validate(updated_lesson)

    async def delete_lesson(self, teacher_user_id: int, lesson_id: int) -> LessonResponseDTO:
        teacher = await self.teacher_repo.get_teacher_by_user_id(teacher_user_id)
        if not teacher:
            raise PermissionErrorService("Teacher not found")

        lesson = await self.lessons_repo.get_lesson_by_id(lesson_id)
        if not lesson:
            raise LessonNotFound("Lesson not found")

        if lesson.teacher_id != teacher.id:
            raise PermissionErrorService("Access denied to delete this lesson")

        deleted_lesson = await self.lessons_repo.delete_lesson(lesson_id)
        await self.session_db.commit()

        return LessonResponseDTO.model_validate(deleted_lesson)
