from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.base.exception import NotFoundData
from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.check_permission.service import ObjectPermissionService
from src.modules.notifications.repository import NotificationsRepository
from src.modules.notifications.models_dto import NotificationResponseDTO, NotificationTargetDTO, UnreadCountDTO


class NotificationsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = NotificationsRepository(session)

    async def homework_event(self, homework_id: int, event: str, submission_id: int | None = None) -> None:
        student, teacher = await self.repo.homework_parties(homework_id)
        target = submission_id if submission_id is not None else homework_id
        kind = "submission" if submission_id is not None else "homework"
        await self.repo.stage(teacher if event == "solution_submitted" else student,
                              event, kind, target, f"{event}:{target}")

    async def lesson_event(self, lesson_id: int, event: str) -> None:
        # Persisted update timestamp identifies this transition, including internal retries.
        version = await self.repo.lesson_event_version(lesson_id)
        key = f"{event}:{lesson_id}:{version}"
        for recipient in await self.repo.lesson_students(lesson_id):
            # Do not notify recipients whose current membership/link no longer grants access.
            try:
                await ObjectPermissionService(self.session).require(recipient, "lesson", lesson_id)
            except (NotFoundData, PermissionErrorService):
                continue
            await self.repo.stage(recipient, event, "lesson", lesson_id, key)

    async def page(self, user_id: int, limit: int, offset: int, unread_only: bool) -> PaginationResponseDTO[NotificationResponseDTO]:
        rows, total = await self.repo.page(user_id, limit, offset, unread_only)
        return PaginationResponseDTO(items=[NotificationResponseDTO.model_validate(r) for r in rows],
                                     total=total, limit=limit, offset=offset)

    async def unread(self, user_id: int) -> UnreadCountDTO:
        return UnreadCountDTO(unread=await self.repo.unread(user_id))

    async def mark_read(self, user_id: int, notification_id: int) -> NotificationResponseDTO:
        try:
            row = await self.repo.mark_read(user_id, notification_id)
            if row is None:
                raise NotFoundData()
            result = NotificationResponseDTO.model_validate(row)
            await self.session.commit()
            return result
        except Exception:
            await self.session.rollback()
            raise

    async def target(self, user_id: int, notification_id: int) -> NotificationTargetDTO:
        row = await self.repo.owned(user_id, notification_id)
        if row is None:
            raise NotFoundData()
        access = ObjectPermissionService(self.session)
        homework_id = None
        try:
            if row.object_type == "lesson":
                await access.require(user_id, "lesson", row.object_id)
            elif row.object_type == "homework":
                await access.homework(user_id, row.object_id)
            elif row.object_type == "submission":
                from src.modules.homework_submissions.repository import HomeworkSubmissionsRepository
                actor = await access.actor(user_id)
                submission = await HomeworkSubmissionsRepository(self.session).get_by_submission_id(row.object_id, actor=actor)
                if submission is None:
                    raise NotFoundData()
                homework_id = submission.homework_id
                await access.homework(user_id, homework_id)
            else:
                raise NotFoundData()
        except (NotFoundData, PermissionErrorService):
            return NotificationTargetDTO(available=False, message="Объект удалён или доступ к нему завершён.")
        return NotificationTargetDTO(available=True, object_type=row.object_type,
                                     object_id=row.object_id, homework_id=homework_id)
