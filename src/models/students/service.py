from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base.exception import ServiceException
from src.models.students.exception import StudentAlreadyExists
from src.models.students.models_dto import StudentsDTO, CreateStudentDTO, UpdateStudentDTO
from src.models.students.repository import StudentRepository


class StudentService:

    def __init__(
        self,
        student_repo: StudentRepository,
        session_db: AsyncSession,
    ):
        self.student_repo = student_repo
        self.session_db = session_db

    async def add_student(
        self,
        data: CreateStudentDTO,
    ) -> StudentsDTO:
        """Добавление нового студента"""
        try:
            student = self.student_repo.add_student(data)
            await self.session_db.commit()
            await self.session_db.refresh(student)
            return StudentsDTO.model_validate(student)
        except Exception as e:
            await self.session_db.rollback()
            if "user_id" in str(e).lower() or "duplicate key" in str(e).lower() or "unique" in str(e).lower():
                raise StudentAlreadyExists("Student for this user already exists") from e
            raise ServiceException() from e

    async def get_student_by_id(self, student_id: int) -> StudentsDTO | None:
        """Получение студента по ID"""
        student = await self.student_repo.get_student_by_id(student_id)
        return StudentsDTO.model_validate(student) if student else None

    async def get_student_by_user_id(self, user_id: int) -> StudentsDTO | None:
        """Получение студента по user_id"""
        student = await self.student_repo.get_student_by_user_id(user_id)
        return StudentsDTO.model_validate(student) if student else None

    async def get_all_students(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[StudentsDTO]:
        """Получение списка всех студентов"""
        students = await self.student_repo.get_all_students(limit=limit, offset=offset)
        return [StudentsDTO.model_validate(student) for student in students]

    async def update_student(
        self,
        student_id: int,
        data: UpdateStudentDTO,
    ) -> StudentsDTO | None:
        """Обновление данных студента по ID"""
        values = data.model_dump(exclude_unset=True)
        if not values:
            return await self.get_student_by_id(student_id)

        student = await self.student_repo.update_student(
            student_id=student_id,
            values=values,
        )
        if student:
            await self.session_db.commit()
            await self.session_db.refresh(student)
            return StudentsDTO.model_validate(student)

        return None

    async def update_student_by_user_id(
        self,
        user_id: int,
        data: UpdateStudentDTO,
    ) -> StudentsDTO | None:
        """Обновление данных студента по user_id"""
        values = data.model_dump(exclude_unset=True)
        if not values:
            return await self.get_student_by_user_id(user_id)

        student = await self.student_repo.update_student_by_user_id(
            user_id=user_id,
            values=values,
        )
        if student:
            await self.session_db.commit()
            await self.session_db.refresh(student)
            return StudentsDTO.model_validate(student)

        return None

    async def delete_student(self, student_id: int) -> StudentsDTO | None:
        """Удаление студента по ID"""
        student = await self.student_repo.delete_student(student_id=student_id)
        if student:
            await self.session_db.commit()
            return StudentsDTO.model_validate(student)

        return None

    async def delete_student_by_user_id(self, user_id: int) -> StudentsDTO | None:
        """Удаление студента по user_id"""
        student = await self.student_repo.delete_student_by_user_id(user_id=user_id)
        if student:
            await self.session_db.commit()
            return StudentsDTO.model_validate(student)

        return None
