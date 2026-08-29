from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base.exception import ServiceException
from src.models.teachers.exception import TeacherAlreadyExists
from src.models.teachers.models_dto import TeachersDTO, CreateTeacherDTO, UpdateTeacherDTO
from src.models.teachers.repository import TeacherRepository


class TeacherService:

    def __init__(
        self,
        teacher_repo: TeacherRepository,
        session_db: AsyncSession,
    ):
        self.teacher_repo = teacher_repo
        self.session_db = session_db

    async def add_teacher(
        self,
        data: CreateTeacherDTO,
    ) -> TeachersDTO:
        """Добавление нового преподавателя"""
        try:
            teacher = self.teacher_repo.add_teacher(data)
            await self.session_db.commit()
            await self.session_db.refresh(teacher)
            return TeachersDTO.model_validate(teacher)
        except Exception as e:
            await self.session_db.rollback()
            if "user_id" in str(e).lower() or "duplicate key" in str(e).lower() or "unique" in str(e).lower():
                raise TeacherAlreadyExists("Teacher for this user already exists") from e
            raise ServiceException() from e

    async def get_teacher_by_id(self, teacher_id: int) -> TeachersDTO | None:
        """Получение преподавателя по ID"""
        teacher = await self.teacher_repo.get_teacher_by_id(teacher_id)
        return TeachersDTO.model_validate(teacher) if teacher else None

    async def get_teacher_by_user_id(self, user_id: int) -> TeachersDTO | None:
        """Получение преподавателя по user_id"""
        teacher = await self.teacher_repo.get_teacher_by_user_id(user_id)
        return TeachersDTO.model_validate(teacher) if teacher else None

    async def get_all_teachers(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> List[TeachersDTO]:
        """Получение списка всех преподавателей"""
        teachers = await self.teacher_repo.get_all_teachers(limit=limit, offset=offset)
        return [TeachersDTO.model_validate(teacher) for teacher in teachers]

    async def update_teacher(
        self,
        teacher_id: int,
        data: UpdateTeacherDTO,
    ) -> TeachersDTO | None:
        """Обновление данных преподавателя по ID"""
        values = data.model_dump(exclude_unset=True)
        if not values:
            return await self.get_teacher_by_id(teacher_id)

        teacher = await self.teacher_repo.update_teacher(
            teacher_id=teacher_id,
            values=values,
        )
        if teacher:
            await self.session_db.commit()
            await self.session_db.refresh(teacher)
            return TeachersDTO.model_validate(teacher)

        return None

    async def update_teacher_by_user_id(
        self,
        user_id: int,
        data: UpdateTeacherDTO,
    ) -> TeachersDTO | None:
        """Обновление данных преподавателя по user_id"""
        values = data.model_dump(exclude_unset=True)
        if not values:
            return await self.get_teacher_by_user_id(user_id)

        teacher = await self.teacher_repo.update_teacher_by_user_id(
            user_id=user_id,
            values=values,
        )
        if teacher:
            await self.session_db.commit()
            await self.session_db.refresh(teacher)
            return TeachersDTO.model_validate(teacher)

        return None

    async def delete_teacher(self, teacher_id: int) -> TeachersDTO | None:
        """Удаление преподавателя по ID"""
        teacher = await self.teacher_repo.delete_teacher(teacher_id=teacher_id)
        if teacher:
            await self.session_db.commit()
            return TeachersDTO.model_validate(teacher)

        return None

    async def delete_teacher_by_user_id(self, user_id: int) -> TeachersDTO | None:
        """Удаление преподавателя по user_id"""
        teacher = await self.teacher_repo.delete_teacher_by_user_id(user_id=user_id)
        if teacher:
            await self.session_db.commit()
            return TeachersDTO.model_validate(teacher)

        return None