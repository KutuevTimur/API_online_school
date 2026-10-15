"""Permanent PostgreSQL regressions for CHECKUP_T13 Q01–Q04."""
from io import BytesIO

import pytest
from PIL import Image
from sqlalchemy import select, update

from tests.modules.auth.test_t06_permissions import world, auth
from src.modules.homework_submissions.models import HomeworkSubmission
from src.modules.courses.models import Course


def photo():
    out = BytesIO()
    Image.new('RGB', (24, 24), 'red').save(out, 'PNG')
    return out.getvalue()


@pytest.mark.asyncio
@pytest.mark.parametrize('target', ['user', 'course'])
@pytest.mark.parametrize('filename', ['traversal', '/absolute.webp', r'C:\outside\photo.webp', 'normal.webp'])
async def test_avatar_invalid_preserves_foreign(client_for_tests, world, target, filename):
    w = world
    victim = w['avatar']; before = victim.read_bytes()
    if filename == 'traversal':
        filename = f"/../../avatars_users/{w['accounts']['s1'][0].id}/avatar.webp"
    url = (f"/users/{w['accounts']['t1'][0].id}/avatar" if target == 'user'
           else f"/courses/{w['courses'][0].id}/avatar")
    r = await client_for_tests.patch(url, headers=auth(w['accounts']['t1'][1]),
                                   files={'avatar': (filename, b'invalid', 'image/webp')})
    assert r.status_code == 400
    assert victim.exists() and victim.read_bytes() == before


@pytest.mark.asyncio
@pytest.mark.parametrize('target', ['user', 'course'])
async def test_avatar_failed_replace_and_success(client_for_tests, world, target):
    w = world; c = client_for_tests
    url = (f"/users/{w['accounts']['s1'][0].id}/avatar" if target == 'user'
           else f"/courses/{w['courses'][0].id}/avatar")
    headers = auth(w['accounts']['s1' if target == 'user' else 't1'][1])
    r = await c.patch(url, headers=headers, files={'avatar': ('ok.png', photo(), 'text/html')})
    assert r.status_code == 200, r.text
    assert r.json()['avatar_path'] == url
    old = await c.get(url, headers=headers)
    assert old.status_code == 200 and old.content.startswith(b'RIFF')
    r = await c.patch(url, headers=headers, files={'avatar': ('bad.png', b'bad', 'image/png')})
    assert r.status_code == 400
    assert (await c.get(url, headers=headers)).content == old.content
    r = await c.patch(url, headers=headers, files={'avatar': ('again.png', photo(), 'image/png')})
    assert r.status_code == 200
    assert (await c.get(url, headers=headers)).content.startswith(b'RIFF')


@pytest.mark.asyncio
@pytest.mark.parametrize('status,working', [('draft', True), ('submitted', True), ('draft', False), ('checked', True)])
async def test_delete_homework_with_any_answer(client_for_tests, world, session_db, status, working):
    w = world
    await session_db.execute(update(HomeworkSubmission).where(HomeworkSubmission.id == w['submissions'][0].id)
                             .values(status=status, is_working=working))
    await session_db.commit()
    from pathlib import Path
    from src.modules.homeworks.models import Homework
    from src.modules.homework_submissions.models import HomeworkSubmissionFile
    from src.modules.homework_placements.models import HomeworkPlacement, HomeworkDeadlineEvent
    from src.modules.course_lifecycle.models import FileDeletion
    models = [Homework, HomeworkSubmission, HomeworkSubmissionFile, HomeworkPlacement, HomeworkDeadlineEvent, FileDeletion]
    async def snapshot():
        return [list((await session_db.scalars(select(model.id).order_by(model.id))).all()) for model in models]
    before = await snapshot()
    files = {Path(f.pdf_file_path): Path(f.pdf_file_path).read_bytes() for f in w['files']}
    r = await client_for_tests.delete(f"/homeworks/{w['homeworks'][0].id}",
        headers=auth(w['accounts']['t1'][1]), params={'lesson_id': w['lessons'][0].id,
        'student_user_id': w['accounts']['s1'][0].id})
    assert r.status_code == 409, r.text
    assert await session_db.scalar(select(HomeworkSubmission.id).where(HomeworkSubmission.id == w['submissions'][0].id))
    assert await snapshot() == before
    assert all(path.read_bytes() == content for path, content in files.items())


@pytest.mark.asyncio
@pytest.mark.parametrize('field', ['name', 'slug', 'avatar_type', 'is_deleted'])
async def test_course_patch_null(client_for_tests, world, session_db, field):
    w = world
    cid = w['courses'][0].id
    column = getattr(Course, field)
    before = await session_db.scalar(select(column).where(Course.id == cid))
    r = await client_for_tests.patch(f"/courses/{w['courses'][0].id}",
        headers=auth(w['accounts']['t1'][1]), json={field: None})
    assert r.status_code == 422, r.text
    assert await session_db.scalar(select(column).where(Course.id == cid)) == before


@pytest.mark.asyncio
async def test_course_patch_bounds_clear_and_duplicate(client_for_tests, world):
    w = world; url = f"/courses/{w['courses'][0].id}"; headers = auth(w['accounts']['t1'][1])
    for field in ['name', 'slug']:
        for value in ['', 'x' * 501]:
            r = await client_for_tests.patch(url, headers=headers, json={field: value})
            assert r.status_code == 422, r.text
    r = await client_for_tests.patch(url, headers=headers, json={'slug': w['courses'][1].slug})
    assert r.status_code == 409
    r = await client_for_tests.patch(url, headers=headers, json={'description': None, 'call_url': None})
    assert r.status_code == 200 and r.json()['description'] is None and r.json()['call_url'] is None


@pytest.mark.asyncio
@pytest.mark.parametrize('target', ['user', 'course'])
@pytest.mark.parametrize('failure', ['write', 'commit', 'cancel', 'unknown_commit'])
async def test_avatar_transaction_failures(world, session_db, user_service_fixture,
        courses_service_fixture, monkeypatch, target, failure, config_fix, client_for_tests):
    import asyncio
    from pathlib import Path
    from fastapi import UploadFile
    from src.modules.storage.service import LocalStorage
    from src.modules.students.models import Student
    from src.modules.account_invitations.models import AccountAudit
    from sqlalchemy import func

    w = world; uid = w['accounts']['s1'][0].id; cid = w['courses'][0].id
    teacher_id = w['teachers'][0].id; admin = w['accounts']['admin'][0]
    service = user_service_fixture if target == 'user' else courses_service_fixture
    # Establish a valid old pointer, including the legacy user path case.
    if target == 'course':
        await service.update_avatar(cid, teacher_id, UploadFile(BytesIO(photo()), filename='old.png'))
        old_path = await session_db.scalar(select(Course.avatar_path).where(Course.id == cid))
    else:
        old_path = str(w['avatar'])
    before = Path(old_path).read_bytes()
    audit_before = await session_db.scalar(select(func.count()).select_from(AccountAudit))
    await session_db.rollback()
    real_commit = session_db.commit
    async def fail_commit():
        await session_db.flush()
        if failure == 'unknown_commit':
            await real_commit()
        raise RuntimeError('injected commit failure')
    real_put = LocalStorage.put
    async def fail_put(self, stream, key, **kwargs):
        if key.startswith('objects/'):
            if failure == 'cancel':
                await real_put(self, stream, key, **kwargs)
                raise asyncio.CancelledError()
            raise OSError('injected write failure')
        return await real_put(self, stream, key, **kwargs)
    with monkeypatch.context() as m:
        if failure in ['commit', 'unknown_commit']:
            m.setattr(session_db, 'commit', fail_commit)
        else:
            m.setattr(LocalStorage, 'put', fail_put)
        expected = asyncio.CancelledError if failure == 'cancel' else (RuntimeError if 'commit' in failure else Exception)
        with pytest.raises(expected):
            upload = UploadFile(BytesIO(photo()), filename='new.png')
            if target == 'user':
                await service.update_avatar(uid, upload, admin)
            else:
                await service.update_avatar(cid, teacher_id, upload)
    if target == 'user':
        current = await session_db.scalar(select(Student.avatar_path).where(Student.user_id == uid))
    else:
        current = await session_db.scalar(select(Course.avatar_path).where(Course.id == cid))
    assert Path(old_path).read_bytes() == before
    if failure == 'unknown_commit':
        assert current != old_path and Path(current).exists()
        assert await session_db.scalar(select(func.count()).select_from(AccountAudit)) == audit_before + (target == 'user')
    else:
        assert current == old_path
        assert await session_db.scalar(select(func.count()).select_from(AccountAudit)) == audit_before
        assert all(not p.exists() for p in service.handler_images.created_paths)
    await session_db.rollback()
    url = f'/users/{uid}/avatar' if target == 'user' else f'/courses/{cid}/avatar'
    r = await client_for_tests.get(url, headers=auth(w['accounts']['s1' if target == 'user' else 't1'][1]))
    assert r.status_code == 200
    assert r.content == (Path(current).read_bytes() if failure == 'unknown_commit' else before)


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['oversize', 'pixels', 'animation', 'timeout', 'symlink'])
async def test_avatar_limits_and_symlink(client_for_tests, world, config_fix, monkeypatch, tmp_path, kind):
    import struct
    import zlib
    w = world; original = w['avatar'].read_bytes()
    uid = w['accounts']['s1'][0].id
    content = photo(); filename = 'photo.png'; expected = 400
    if kind == 'oversize':
        monkeypatch.setattr(config_fix, 'avatar_max_bytes', 8)
        expected = 413
    elif kind == 'pixels':
        ihdr = struct.pack('>IIBBBBB', 10000, 10000, 8, 2, 0, 0, 0)
        content = content[:16] + ihdr + struct.pack('>I', zlib.crc32(b'IHDR'+ihdr)) + content[33:]
    elif kind == 'animation':
        out = BytesIO()
        Image.new('RGB', (10,10), 'red').save(out, 'WEBP', save_all=True,
            append_images=[Image.new('RGB', (10,10), 'blue')], duration=100, loop=0)
        content = out.getvalue(); filename = 'animated.webp'
    elif kind == 'timeout':
        monkeypatch.setattr(config_fix, 'avatar_processing_timeout_seconds', 0.001)
    elif kind == 'symlink':
        root = config_fix.paths.objects
        saved = root.with_name('saved-objects')
        root.rename(saved)
        root.symlink_to(tmp_path, target_is_directory=True)
    try:
        r = await client_for_tests.patch(f'/users/{uid}/avatar', headers=auth(w['accounts']['s1'][1]),
            files={'avatar': (filename, content, 'image/png')})
        assert r.status_code == expected, r.text
        assert w['avatar'].read_bytes() == original
        assert list(tmp_path.iterdir()) == []
    finally:
        if kind == 'symlink':
            root.unlink(); saved.rename(root)


@pytest.mark.asyncio
async def test_avatar_remove_missing_bytes_retry(client_for_tests, world):
    w = world; uid = w['accounts']['s1'][0].id
    w['avatar'].unlink()
    url = f'/users/{uid}/avatar'; headers = auth(w['accounts']['s1'][1])
    assert (await client_for_tests.delete(url, headers=headers)).status_code == 204
    assert (await client_for_tests.get(url, headers=headers)).status_code == 404
    assert (await client_for_tests.delete(url, headers=headers)).status_code == 404


@pytest.mark.asyncio
async def test_avatar_cleanup_failure_is_durable(client_for_tests, world, session_db, config_fix, monkeypatch):
    from pathlib import Path
    from src.modules.storage.service import LocalStorage
    from src.modules.course_lifecycle.models import FileDeletion
    from src.modules.course_lifecycle.service import LifecycleService
    from src.modules.course_lifecycle.repository import LifecycleRepository
    w = world; old = w['avatar']; uid = w['accounts']['s1'][0].id
    def fail_delete(self, key):
        raise OSError('injected unlink failure')
    with monkeypatch.context() as m:
        m.setattr(LocalStorage, '_delete', fail_delete)
        r = await client_for_tests.patch(f'/users/{uid}/avatar', headers=auth(w['accounts']['s1'][1]),
            files={'avatar': ('ok.png', photo(), 'image/png')})
        assert r.status_code == 200
    assert old.exists()
    job = await session_db.scalar(select(FileDeletion).where(FileDeletion.path == str(old)))
    assert job is not None and not job.completed and job.attempts >= 1
    await session_db.rollback()
    service = LifecycleService(LifecycleRepository(session_db), config_fix)
    await service._cleanup(100)
    assert not old.exists()
    await service._cleanup(100)  # retry is harmless
    assert (await client_for_tests.get(f'/users/{uid}/avatar', headers=auth(w['accounts']['s1'][1]))).status_code == 200


@pytest.mark.asyncio
async def test_avatar_get_rejects_symlink(client_for_tests, world, tmp_path):
    w = world; victim = w['avatar']; uid = w['accounts']['s1'][0].id
    secret = tmp_path/'private'; secret.write_bytes(b'private synthetic bytes')
    victim.unlink(); victim.symlink_to(secret)
    r = await client_for_tests.get(f'/users/{uid}/avatar', headers=auth(w['accounts']['s1'][1]))
    assert r.status_code == 404 and secret.read_bytes() == b'private synthetic bytes'


@pytest.mark.asyncio
async def test_delete_homework_serializes_against_answer_create(world, config_fix, session_db):
    """Hold the same parent course lock used by answer creation, then DELETE."""
    import asyncio
    from sqlalchemy import delete
    from src.modules.homework_submissions.models import HomeworkSubmissionFile
    from src.modules.homework_submissions.depends import get_homework_submissions_service
    from src.modules.homeworks.depends import get_homeworks_service
    from src.modules.course_lifecycle.repository import LifecycleRepository
    from src.modules.base.exception import NotFoundData
    from src.modules.homeworks.models import Homework
    w = world; hid = w['homeworks'][0].id; cid = w['courses'][0].id
    sid = w['accounts']['s1'][0].id; tid = w['accounts']['t1'][0].id; lid = w['lessons'][0].id
    await session_db.execute(delete(HomeworkSubmissionFile).where(HomeworkSubmissionFile.submission_id == w['submissions'][0].id))
    await session_db.execute(delete(HomeworkSubmission).where(HomeworkSubmission.id == w['submissions'][0].id))
    await session_db.commit()
    started = asyncio.Event()
    async def create():
        async with config_fix.db_connection.session_local() as session:
            started.set()
            try:
                await get_homework_submissions_service(session=session, config=config_fix).create_submission(sid, hid, 'answer')
            except NotFoundData:
                await session.rollback()
                return 'not_found'
            return 'created'
    async with config_fix.db_connection.session_local() as session:
        await LifecycleRepository(session).course(cid)
        task = asyncio.create_task(create())
        await started.wait()
        try:
            await get_homeworks_service(session=session, config=config_fix).delete_homework(tid, lid, sid, hid)
        finally:
            await session.rollback()
        assert await asyncio.wait_for(task, 10) == 'not_found'
    assert await session_db.scalar(select(Homework.id).where(Homework.id == hid)) is None
