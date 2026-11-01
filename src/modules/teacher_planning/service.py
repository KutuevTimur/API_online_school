from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from src.modules.teacher_planning.repository import TeacherPlanningRepository
from src.modules.teacher_planning.models_dto import UpdateLessonPriceDTO, LessonPriceDTO, WeeklyEarningsDTO, PlanningStudentDTO, RecipientReminderDTO, NormRequestDTO, ReminderRequestDTO
from src.modules.users.models_dto import UserDTO
from src.modules.teacher_planning.models import WeeklyLessonNorm
from src.modules.base.exception import StaleUpdate
from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.check_permission.service import ObjectPermissionService
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.lessons.exception import InvalidLessonRequest


def effective_norm(rows: list[WeeklyLessonNorm], week: date) -> tuple[int | None, bool]:
    regular = next((r for r in reversed(rows) if r.kind == 'regular' and r.week <= week), None)
    exception = next((r for r in rows if r.kind == 'exception' and r.week == week), None)
    row = exception or regular
    return (row.target, row.paused) if row else (None, False)


class TeacherPlanningService:
    def __init__(self, repo: TeacherPlanningRepository) -> None:
        self.repo = repo
        self.session = repo.session

    async def students(self, actor: UserDTO, week: date, q: str | None, limit: int, offset: int, student_user_id: int | None = None, deficit_only: bool = False) -> PaginationResponseDTO[PlanningStudentDTO]:
        if week.weekday() != 0:
            raise InvalidLessonRequest('Use Monday of the Moscow week')
        try:
            rows, norms, total = await self.repo.students(actor.id, week, q, limit, offset, student_user_id, deficit_only)
        except OverflowError as exc:
            raise InvalidLessonRequest('Week is outside the supported calendar range') from exc
        items = []
        for row in rows:
            target, paused = effective_norm([r for r in norms if r.student_id == row['student_id']], week)
            items.append(PlanningStudentDTO(**{k: row[k] for k in ('user_id', 'first_name', 'last_name',
                'username', 'scheduled_count', 'missing_homework', 'missing_lecture', 'norm_revision')},
                target=target, paused=paused))
        return PaginationResponseDTO(items=items, total=total, limit=limit, offset=offset)

    async def norm(self, actor: UserDTO, student_user_id: int, data: NormRequestDTO) -> dict[str, int]:
        try:
            pair = await self.repo.linked_pair(actor.id, student_user_id)
            if pair is None:
                raise PermissionErrorService()
            today = datetime.now(ZoneInfo('Europe/Moscow')).date()
            monday = today - timedelta(days=today.weekday())
            if data.week < monday + (timedelta(days=7) if data.kind == 'regular' else timedelta()):
                raise InvalidLessonRequest('Regular norm starts next week; current week needs an exception; past weeks are immutable')
            if data.expected_revision != pair.planning_revision:
                raise StaleUpdate('Norm changed; reload before saving')
            await self.repo.write_norm(pair, data)
            pair.planning_revision += 1
            revision = pair.planning_revision
            await self.session.commit()
            return {'revision': revision}
        except Exception:
            await self.session.rollback()
            raise

    async def reminders(self, actor: UserDTO, lesson_id: int | None, student_user_id: int | None, limit: int, offset: int, only_missing: bool) -> PaginationResponseDTO[RecipientReminderDTO]:
        rows, total = await self.repo.reminders(actor.id, lesson_id, student_user_id, limit, offset, only_missing)
        return PaginationResponseDTO(items=[RecipientReminderDTO(**r) for r in rows], total=total, limit=limit, offset=offset)

    async def mark(self, actor: UserDTO, lesson_id: int, student_user_id: int, data: ReminderRequestDTO) -> PaginationResponseDTO[RecipientReminderDTO]:
        try:
            await ObjectPermissionService(self.session).require(actor.id, 'lesson', lesson_id, write=True)
            recipient = await self.repo.recipient(actor.id, lesson_id, student_user_id)
            if recipient is None:
                raise PermissionErrorService()
            rows, _ = await self.repo.reminders(actor.id, lesson_id, student_user_id, 1, 0, False)
            if not rows:
                raise PermissionErrorService()
            for key, value in data.model_dump(exclude_unset=True).items():
                if value is None:
                    raise InvalidLessonRequest('A boolean value is required')
                setattr(recipient, key, value)
            await self.session.commit()
            return await self.reminders(actor, lesson_id, student_user_id, 1, 0, False)
        except Exception:
            await self.session.rollback()
            raise

    async def price(self, actor: UserDTO, student_user_id: int, data: "UpdateLessonPriceDTO | None" = None) -> "LessonPriceDTO":
        from src.modules.users.models import UserRole
        if actor.role != UserRole.TEACHER:
            raise PermissionErrorService()
        from src.modules.lessons.repository import LessonsRepository
        from src.modules.teacher_planning.models_dto import LessonPriceDTO
        try:
            # Same lock order as single/regular creation: schedule -> active pair.
            if data is not None:
                await LessonsRepository(self.session).lock_schedule(actor.id)
            pair = await self.repo.linked_pair(actor.id, student_user_id)
            if pair is None:
                raise PermissionErrorService()
            if data is not None:
                if pair.lesson_price_kopecks != data.expected_price_kopecks:
                    raise StaleUpdate('Price changed; reload before saving')
                pair.lesson_price_kopecks = data.lesson_price_kopecks
            result = LessonPriceDTO(lesson_price_kopecks=pair.lesson_price_kopecks)
            await self.session.commit()
            return result
        except Exception:
            await self.session.rollback()
            raise

    async def weekly_earnings(self, actor: UserDTO, week: date) -> "WeeklyEarningsDTO":
        from src.modules.users.models import UserRole
        if actor.role != UserRole.TEACHER:
            raise PermissionErrorService()
        if week.weekday() != 0:
            raise InvalidLessonRequest('Use Monday of the Moscow week')
        try:
            row = await self.repo.weekly_earnings(actor.id, week)
        except OverflowError as exc:
            raise InvalidLessonRequest('Week is outside the supported calendar range') from exc
        return WeeklyEarningsDTO(week=week, **row)
