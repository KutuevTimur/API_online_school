"""Queue context and batch behavior, no DB connection or clearing fixtures."""
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.dialects import postgresql

from src.modules.homework_submissions.models_dto import HomeworkSubmissionResponseDTO
from src.modules.homework_submissions.repository import HomeworkSubmissionsRepository
from src.modules.homework_submissions.service import HomeworkSubmissionsService
from src.modules.users.models import UserRole


@pytest.mark.asyncio
async def test_queue_context_and_file_descriptors_are_one_batch():
    now = datetime.now(UTC)
    answers = [HomeworkSubmissionResponseDTO(
        id=i, homework_id=i + 10, attempt_number=1, version=3,
        text_content='Synthetic answer', status='submitted',
        created_at=now, updated_at=now, submitted_at=now,
        files=[dict(id=i + 20, original_file_name='photo.png', created_at=now)],
    ) for i in [1, 2]]
    # ORM source includes asset ids, while the public response deliberately does not.
    orm = [SimpleNamespace(**a.model_dump(exclude={'files'}), files=[SimpleNamespace(
        id=a.id + 20, download_asset_id=a.id + 100, pdf_file_name=None,
        original_file_name='photo.png', created_at=now,
    )]) for a in answers]
    repo = SimpleNamespace(review_queue=AsyncMock(return_value=(
        [(a, 30, 40, 50, 'Homework', 'Synthetic', 'Student', 'synthetic', 'Course') for a in orm], 2)))
    service = HomeworkSubmissionsService(repo, None, None, None, None, None, None)
    with patch('src.modules.homework_submissions.service.ObjectPermissionService') as permission, patch(
        'src.modules.files.service.file_descriptors', new_callable=AsyncMock, return_value={}
    ) as descriptors:
        permission.return_value.actor = AsyncMock(return_value=SimpleNamespace(role=UserRole.TEACHER))
        result = await service.review_queue(70, 20, 0, 30, 50)
        repo.review_queue.assert_awaited_once_with(70, 20, 0, 30, 50)
        descriptors.assert_awaited_once()
        assert len(descriptors.call_args.args[1]) == 2
        assert result.total == 2
        assert result.items[0].student_first_name == 'Synthetic'
        assert result.items[0].course_name == 'Course'
        assert result.items[0].student_username == 'synthetic'
        assert result.items[0].checked_by is None
        assert 'file_path' not in result.model_dump_json()


@pytest.mark.asyncio
async def test_queue_statement_preserves_scope_context_and_snapshot_count():
    result = SimpleNamespace(all=lambda: [(None, None, None, None, None, None, None, None, None, 0)])
    session = SimpleNamespace(execute=AsyncMock(return_value=result))
    repo = HomeworkSubmissionsRepository(session)
    rows, total = await repo.review_queue(77, 20, 40, course_id=33, student_user_id=55)
    assert rows == [] and total == 0
    sql = str(session.execute.call_args.args[0].compile(dialect=postgresql.dialect()))
    assert 'queue_first_name' in sql and 'queue_username' in sql and 'queue_course_name' in sql
    assert 'LEFT OUTER JOIN' in sql and 'count(' in sql
    assert 'teacher_students' in sql and 'history_revoked' in sql and 'access_ended_at' in sql
    params = session.execute.call_args.args[0].compile(dialect=postgresql.dialect()).params
    assert 77 in params.values() and 33 in params.values() and 55 in params.values()
