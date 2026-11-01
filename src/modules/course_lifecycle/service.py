from pathlib import Path
from uuid import uuid4
from src.core.config import Config
from src.modules.base.exception import NotFoundData
from src.modules.check_permission.service import ObjectPermissionService
from src.modules.check_permission.exception import PermissionErrorService
from src.modules.course_lifecycle.repository import LifecycleRepository
from src.modules.course_lifecycle.models import LifecycleAudit
from src.modules.course_lifecycle.exception import InvalidPurgeConfirmation
from src.modules.users.models import UserRole
from src.modules.courses.models_dto import CoursesResponseDTO
from src.modules.lessons.models_dto import LessonResponseDTO
from src.modules.course_lifecycle.models_dto import CleanupResponse, PurgeResponse, PurgeCourseRequest


class LifecycleService:
    def __init__(self, repository: LifecycleRepository, config: Config) -> None:
        self.repo = repository
        self.session = repository.session
        self.config = config

    async def admin(self, actor_id: int) -> None:
        actor = await ObjectPermissionService(self.session).actor(actor_id)
        if actor.role != UserRole.ADMIN:
            raise PermissionErrorService()

    def audit(self, actor_id: int, kind: str, object_id: int, action: str) -> None:
        self.session.add(LifecycleAudit(actor_user_id=actor_id, object_type=kind,
                                       object_id=object_id, action=action, correlation_id=uuid4().hex))

    async def restore(self, actor_id: int, kind: str, object_id: int) -> CoursesResponseDTO | LessonResponseDTO:
        await self.admin(actor_id)
        try:
            schedule_course_id = object_id if kind == 'course' else await self.repo.lesson_course_id(object_id)
            if schedule_course_id is not None:
                await self.repo.lock_schedule_for_course(schedule_course_id)
            if kind == 'course':
                obj = await self.repo.course(object_id)
            else:
                # Course first, same lock order as writes and purge.
                course_id = await self.repo.lesson_course_id(object_id)
                if course_id is None:
                    raise NotFoundData()
                await self.repo.course(course_id)
                obj = await self.repo.lesson(object_id)
            if obj is None:
                raise NotFoundData()
            if obj.is_deleted:
                obj.restore()
                self.audit(actor_id, kind, object_id, 'restore')
            from src.modules.homework_placements.service import HomeworkPlacementsService
            await HomeworkPlacementsService(self.session).recalculate_course(
                obj.id if kind == "course" else obj.course_id, kind + "_restored")
            # Flush expires both the timestamp and a lesson's computed status.
            # Load them inside the async context before DTO attribute access.
            attributes = ["updated_at"] + (["effective_status"] if kind == "lesson" else [])
            await self.session.refresh(obj, attribute_names=attributes)
            dto = (CoursesResponseDTO if kind == 'course' else LessonResponseDTO).model_validate(obj)
            await self.session.commit()
            return dto
        except Exception:
            await self.session.rollback()
            raise

    async def history_access(self, actor_id: int, course_id: int, user_id: int, revoked: bool) -> None:
        await self.admin(actor_id)
        try:
            if await self.repo.course(course_id) is None:
                raise NotFoundData()
            enrollment = await self.repo.enrollment(course_id, user_id)
            if enrollment is None:
                raise NotFoundData()
            enrollment.history_revoked = revoked
            self.audit(actor_id, 'enrollment', enrollment.id, 'revoke_history' if revoked else 'restore_history')
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise

    async def purge(self, actor_id: int, course_id: int, confirmation: PurgeCourseRequest) -> PurgeResponse:
        await self.admin(actor_id)
        try:
            course = await self.repo.course(course_id)
            if course is None:
                raise NotFoundData()
            if confirmation.confirm_course_id != course_id or confirmation.confirm_name != course.name:
                raise InvalidPurgeConfirmation()
            self.audit(actor_id, 'course', course_id, 'purge')
            await self.repo.purge(course_id)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        # Failures here must leave committed jobs retryable; never roll back target deletion.
        from src.modules.files.maintenance import queue_purged_backups
        await queue_purged_backups(self.config,self.session)
        cleanup = await self.cleanup(actor_id, 100)
        return PurgeResponse(course_id=course_id, cleanup=cleanup)

    def safe_path(self, raw: str) -> Path:
        from src.modules.storage.service import LegacyStorage
        path = Path(raw)
        roots = [self.config.paths.avatars_users, self.config.paths.avatars_courses, self.config.paths.lectures,
                 self.config.paths.homework, self.config.paths.homework_submissions, self.config.paths.temp,
                 self.config.paths.objects]
        LegacyStorage(self.config.paths).key(path)
        if not any(path.is_relative_to(root) and path != root for root in roots):
            raise ValueError('unsafe_path')
        return path

    async def cleanup(self, actor_id: int, limit: int) -> CleanupResponse:
        await self.admin(actor_id)
        return await self._cleanup(limit)

    async def _cleanup(self, limit: int) -> CleanupResponse:
        completed = failed = 0
        try:
            jobs = await self.repo.pending(limit)
            referenced = {Path(p) for p in await self.repo.referenced_paths()}
            referenced.update(self.config.paths.media / key for key in await self.repo.asset_keys())
            from src.modules.files.maintenance import retained_paths
            referenced.update(await retained_paths(self.config,self.session))
            for job in jobs:
                job.attempts += 1
                try:
                    path = self.safe_path(job.path)
                    if path in referenced:
                        # Still shared: retain job, recheck on the next run.
                        job.last_error = 'referenced'
                        failed += 1
                        continue
                    from src.modules.storage.service import LocalStorage, LegacyStorage
                    await LocalStorage(self.config.paths).delete(LegacyStorage(self.config.paths).key(path))
                    job.completed = True
                    job.last_error = None
                    completed += 1
                except (OSError, ValueError):
                    job.last_error = 'cleanup_failed'
                    failed += 1
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return CleanupResponse(completed=completed, failed=failed)
