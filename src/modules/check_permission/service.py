from typing import Literal
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.users.models import User
from src.modules.lesson_students.models import LessonStudent
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.users.models import UserRole
from src.modules.users.models_dto import UserDTO


class StudentPermissionService:

    @staticmethod
    def check_role_and_id(
        current_user: UserDTO,
        target_user_id: int,
    ) -> None:
        """
        :exception PermissionErrorService: Если пользователь не admin и ``current_user.id`` != ``target_user_id``
        """
        if current_user.role in {
            UserRole.ADMIN,
        }:
            return

        if current_user.id == target_user_id:
            return

        raise PermissionErrorService()

    @staticmethod
    def check_role(
        current_user: UserDTO,
    ) -> None:
        """
        :exception PermissionErrorService: Если пользователь не является учителем
        """
        if current_user.role in {
            UserRole.TEACHER,
        }:
            return

        raise PermissionErrorService()



class ObjectPermissionService:
    """Fail closed before loading files or performing any domain mutation."""

    def __init__(self, session: AsyncSession) -> None:
        from src.modules.check_permission.repository import PermissionRepository
        self.repo = PermissionRepository(session)

    async def actor(self, user_id: int) -> User:
        actor = await self.repo.actor(user_id)
        if actor is None or not actor.is_active or not actor.is_activated:
            raise PermissionErrorService()
        return actor

    async def require(self, user_id: int, kind: Literal["course", "lesson", "profile"], object_id: int, write: bool = False) -> User:
        from src.modules.base.exception import NotFoundData
        from src.modules.check_permission.repository import course_scope, lesson_scope, profile_scope
        from src.modules.courses.models import Course
        from src.modules.lessons.models import Lesson
        from src.modules.users.models import User
        actor = await self.actor(user_id)
        model, scope = {"course": (Course, course_scope), "lesson": (Lesson, lesson_scope),
                        "profile": (User, profile_scope)}[kind]
        if not await self.repo.visible(model, object_id, scope(actor.id, actor.role)):
            raise NotFoundData()
        if write and ((kind == "profile" and actor.role != UserRole.ADMIN and actor.id != object_id)
                      or (kind != "profile" and actor.role != UserRole.TEACHER)):
            raise PermissionErrorService()
        if write and kind == "course" and not await self.repo.writable_course(object_id):
            raise PermissionErrorService("Archived course is read-only")
        if write and kind == "lesson" and not await self.repo.writable_lesson(object_id):
            raise PermissionErrorService("Archived lesson is read-only")
        return actor

    async def recipient(self, user_id: int, lesson_id: int, student_user_id: int, write: bool = False) -> LessonStudent:
        from src.modules.base.exception import NotFoundData
        actor = await self.actor(user_id)
        recipient = await self.repo.recipient(actor, lesson_id, student_user_id)
        if recipient is None:
            raise NotFoundData()
        if write and actor.role != UserRole.TEACHER:
            raise PermissionErrorService()
        if write and not await self.repo.writable_recipient(recipient):
            raise PermissionErrorService("History is read-only")
        return recipient

    async def homework(self, user_id: int, homework_id: int, expected_role: UserRole | None = None) -> LessonStudent:
        from src.modules.base.exception import NotFoundData
        actor = await self.actor(user_id)
        recipient = await self.repo.homework_recipient(homework_id, actor)
        if recipient is None:
            raise NotFoundData()
        from src.modules.homeworks.models import Homework
        if not await self.repo.material_visible(Homework, homework_id, actor):
            raise NotFoundData()
        if expected_role is not None and not await self.repo.writable_recipient(recipient):
            raise PermissionErrorService("History is read-only")
        if expected_role is not None and actor.role != expected_role:
            raise PermissionErrorService()
        return recipient

    async def require_link(self, teacher_user_id: int, student_user_id: int) -> None:
        from src.modules.base.exception import NotFoundData
        if not await self.repo.linked(teacher_user_id, student_user_id):
            raise NotFoundData()
