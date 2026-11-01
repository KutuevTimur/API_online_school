"""Versioned lesson inverses: pure service mocks, no engine/DB/fixtures."""
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
import pytest
from src.modules.lessons.models import LessonStatus
from src.modules.lessons.models_dto import UpdateLessonRequestDTO
from src.modules.lessons.service import LessonsService
from src.modules.base.exception import StaleUpdate

@pytest.mark.asyncio
@pytest.mark.parametrize('previous,target,event', [
    (LessonStatus.CANCELLED, LessonStatus.SCHEDULED, 'lesson_restored'),
    (LessonStatus.CANCELLED, LessonStatus.COMPLETED, 'lesson_restored'),
    (LessonStatus.SCHEDULED, LessonStatus.CANCELLED, 'lesson_cancelled'),
    (LessonStatus.SCHEDULED, LessonStatus.SCHEDULED, None),
])
async def test_status_transition_notifies_only_once_after_version_check(previous, target, event):
    stamp = datetime(2026, 10, 29, tzinfo=UTC)
    lesson = SimpleNamespace(id=4, teacher_id=9, course_id=3, status=previous,
                             scheduled_at=stamp, duration_minutes=55, updated_at=stamp)
    repo = SimpleNamespace(lock_schedule=AsyncMock(), get_lesson_by_id=AsyncMock(return_value=lesson), update_lesson=AsyncMock())
    session = SimpleNamespace(flush=AsyncMock(), commit=AsyncMock(), rollback=AsyncMock())
    teacher = SimpleNamespace(get_teacher_by_user_id=AsyncMock(return_value=SimpleNamespace(id=9)))
    service = LessonsService(repo, None, None, teacher, session)
    service._write_response = AsyncMock(return_value='saved')
    with patch('src.modules.lessons.service.ObjectPermissionService') as permission, patch('src.modules.lessons.service.HomeworkPlacementsService') as placements, patch('src.modules.notifications.service.NotificationsService') as notices:
        permission.return_value.require = AsyncMock()
        placements.return_value.recalculate_course = AsyncMock()
        notices.return_value.lesson_event = AsyncMock()
        assert await service.update_lesson(10, 4, UpdateLessonRequestDTO(status=target, expected_updated_at=stamp)) == 'saved'
        if event:
            notices.return_value.lesson_event.assert_awaited_once_with(4, event)
        else:
            notices.return_value.lesson_event.assert_not_awaited()
        placements.return_value.recalculate_course.assert_awaited_once_with(3, 'lesson_updated')
        session.commit.assert_awaited_once()
        notices.return_value.lesson_event.reset_mock()
        with pytest.raises(StaleUpdate):
            await service.update_lesson(10, 4, UpdateLessonRequestDTO(status=target, expected_updated_at=stamp-timedelta(seconds=1)))
        notices.return_value.lesson_event.assert_not_awaited()
        session.rollback.assert_awaited_once()
