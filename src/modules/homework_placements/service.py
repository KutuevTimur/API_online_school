from datetime import UTC, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.homework_placements.models import HomeworkPlacement, HomeworkDeadlineEvent
from src.modules.homework_placements.repository import HomeworkPlacementsRepository
from src.modules.homework_placements.models_dto import PlacementResponseDTO, DeadlineEventResponseDTO
from src.modules.check_permission.service import ObjectPermissionService
from src.modules.users.models import UserRole
from src.modules.homework_placements.exception import HomeworkPlacementConflict
from src.modules.homeworks.models import Homework
from src.modules.users.models import User


class HomeworkPlacementsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo = HomeworkPlacementsRepository(session)

    def record(self, placement: HomeworkPlacement, reason: str) -> None:
        self.session.add(HomeworkDeadlineEvent(placement_id=placement.id,
            lesson_student_id=placement.lesson_student_id, due_lesson_id=placement.due_lesson_id,
            due_at=placement.due_at, reason=reason, created_at=datetime.now(UTC)))

    async def original(self, homework: Homework, reason: str = "assigned") -> HomeworkPlacement:
        placement = HomeworkPlacement(homework_id=homework.id, lesson_student_id=homework.lesson_student_id,
                                      kind="original")
        self.session.add(placement)
        await self.session.flush()
        await self.recalculate_one(placement, reason, initial=True)
        homework.deadline = placement.due_at
        return placement

    async def recalculate_one(self, placement: HomeworkPlacement, reason: str, initial: bool = False) -> None:
        recipient, lesson = await self.repo.context(placement.lesson_student_id)
        # Archived and detached placements are historical, not editable schedule entries.
        if not initial and (lesson.is_deleted or recipient.access_ended_at is not None):
            return
        candidate = await self.repo.candidate(recipient, lesson)
        due_id, due_at = (candidate.id, candidate.scheduled_at) if candidate else (None, None)
        if initial or (placement.due_lesson_id, placement.due_at) != (due_id, due_at):
            placement.due_lesson_id, placement.due_at = due_id, due_at
            self.record(placement, reason)

    async def recalculate_course(self, course_id: int, reason: str) -> None:
        # Caller holds Course lock, the same parent lock as answer review/mutations.
        await self.session.flush()
        if not await self.repo.course_active(course_id):
            return
        for homework in await self.repo.course_homeworks(course_id):
            if homework.deadline_frozen_at is not None or await self.repo.checked(homework.id):
                continue
            recipient, lesson = await self.repo.context(homework.lesson_student_id)
            permissions = ObjectPermissionService(self.session)
            if lesson.is_deleted or not await permissions.repo.active_recipient(recipient, course_id):
                continue
            placements = await self.repo.placements(homework.id)
            for placement in placements:
                await self.recalculate_one(placement, reason)
            if placements:
                homework.deadline = placements[-1].due_at
        await self.session.flush()

    async def freeze(self, homework_id: int) -> None:
        homework = await self.repo.homework(homework_id)
        placements = await self.repo.placements(homework_id)
        if not placements:
            placements = [await self.original(homework)]
        homework.deadline = placements[-1].due_at
        homework.deadline_frozen_at = datetime.now(UTC)
        for placement in placements:
            self.record(placement, "checked")
        await self.session.flush()

    async def add_debt(self, teacher_user_id: int, homework_id: int, lesson_id: int) -> PlacementResponseDTO:
        permissions = ObjectPermissionService(self.session)
        try:
            origin = await permissions.homework(teacher_user_id, homework_id, expected_role=UserRole.TEACHER)
            homework = await self.repo.homework(homework_id)
            student = origin.student_user_id
            target = await permissions.recipient(teacher_user_id, lesson_id, student)
            _, origin_lesson = await self.repo.context(origin.id)
            _, target_lesson = await self.repo.context(target.id)
            if origin_lesson.course_id != target_lesson.course_id:
                raise HomeworkPlacementConflict("Debt must stay in the same course and student")
            await permissions.recipient(teacher_user_id, lesson_id, student, write=True)
            placements = await self.repo.placements(homework_id)
            if homework.deadline_frozen_at is not None or await self.repo.checked(homework_id):
                raise HomeworkPlacementConflict("Checked homework cannot become debt")
            if not placements:
                placements = [await self.original(homework)]
            existing = next((p for p in placements if p.lesson_student_id == target.id), None)
            if existing is not None and existing.kind == "debt":
                result = await self.response(existing, await permissions.actor(teacher_user_id), False)
            else:
                _, latest_lesson = await self.repo.context(placements[-1].lesson_student_id)
                if (target_lesson.scheduled_at, target_lesson.id) <= max(
                    (origin_lesson.scheduled_at, origin_lesson.id),
                    (latest_lesson.scheduled_at, latest_lesson.id),
                ):
                    raise HomeworkPlacementConflict("Debt requires a later lesson than the current placement")
                placement = HomeworkPlacement(homework_id=homework_id, lesson_student_id=target.id, kind="debt")
                self.session.add(placement)
                await self.session.flush()
                await self.recalculate_one(placement, "debt_added", initial=True)
                homework.deadline = placement.due_at
                await self.session.flush()
                result = await self.response(placement, await permissions.actor(teacher_user_id), False)
            await self.session.commit()
            return result
        except Exception:
            await self.session.rollback()
            raise

    async def response(self, placement: HomeworkPlacement, actor: User, frozen: bool) -> PlacementResponseDTO:
        events = await self.repo.events(placement.id, actor)
        _, lesson = await self.repo.context(placement.lesson_student_id)
        # Use the last visible journal snapshot to preserve history after cutoff/re-enrollment gaps.
        event = events[-1] if events else None
        return PlacementResponseDTO(id=placement.id, homework_id=placement.homework_id,
            lesson_id=lesson.id, kind=placement.kind, due_lesson_id=event.due_lesson_id if event else None,
            due_at=event.due_at if event else None, created_at=placement.created_at,
            frozen=frozen, events=[DeadlineEventResponseDTO.model_validate(e) for e in events])

    async def history(self, user_id: int, homework_id: int) -> list[PlacementResponseDTO]:
        permissions = ObjectPermissionService(self.session)
        await permissions.homework(user_id, homework_id)
        actor = await permissions.actor(user_id)
        frozen = await self.repo.working_status(homework_id, actor) == "checked"
        return [await self.response(p, actor, frozen)
                for p in await self.repo.placements(homework_id, actor)]
