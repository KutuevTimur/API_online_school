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
        cleanup = await self.cleanup(actor_id, 100)
        return PurgeResponse(course_id=course_id, cleanup=cleanup)

    def safe_path(self, raw: str) -> Path:
        path = Path(raw)
        roots = [self.config.paths.avatars_courses, self.config.paths.lectures,
                 self.config.paths.homework, self.config.paths.homework_submissions]
        resolved = path.resolve()
        if path.is_symlink() or not any(resolved.is_relative_to(root.resolve()) and resolved != root.resolve()
                                        for root in roots):
            raise ValueError('unsafe_path')
        return resolved

    async def cleanup(self, actor_id: int, limit: int) -> CleanupResponse:
        await self.admin(actor_id)
        completed = failed = 0
        try:
            jobs = await self.repo.pending(limit)
            referenced = {Path(p).resolve() for p in await self.repo.referenced_paths()}
            for job in jobs:
                job.attempts += 1
                try:
                    path = self.safe_path(job.path)
                    if path in referenced:
                        # Still shared: retain job, recheck on the next run.
                        job.last_error = 'referenced'
                        failed += 1
                        continue
                    path.unlink(missing_ok=True)
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
