import hashlib
from io import BytesIO
from pathlib import Path

import pytest
from fastapi import UploadFile
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.files.models import FileAsset
from src.modules.homework_submissions.models import HomeworkSubmissionFile
from src.modules.lectures.models import Lecture
from src.modules.homeworks.models import Homework
from src.tools.synthetic_files import pdf_bytes
from tests.modules.auth.test_t06_permissions import world, auth
from tests.modules.homework_submissions.test_t09_lifecycle import route, headers


@pytest.mark.asyncio
async def test_asset_metadata_pdf_single_copy_stable_domain_download(client_for_tests, world, session_db, config_fix):
    data = pdf_bytes('private source')
    r = await client_for_tests.patch(route(world, '/student'), headers=headers(world),
        files={'files': ('../../private-name.pdf', data, 'text/html')})
    assert r.status_code == 200, r.text
    public = r.json()['files'][-1]
    assert 'path' not in str(public) and 'sha256' not in public
    assert public['original_file_name'] == 'private-name.pdf'
    row = await session_db.get(HomeworkSubmissionFile, public['id'])
    assert row.original_asset_id == row.download_asset_id
    assert row.original_file_path == row.pdf_file_path
    asset = await session_db.get(FileAsset, row.original_asset_id)
    assert asset.backend == 'local' and asset.state == 'ready'
    assert asset.mime == 'application/pdf' and asset.size == len(data)
    assert asset.sha256 == hashlib.sha256(data).hexdigest()
    assert asset.uploader_user_id == world['accounts']['s1'][0].id
    assert 'private-name' not in asset.key and '..' not in asset.key
    assert (config_fix.paths.media / asset.key).read_bytes() == data
    download = route(world, f"/files/{row.id}")
    r = await client_for_tests.get(download, headers={**headers(world), 'Range': 'bytes=0-4'})
    assert r.status_code == 206 and r.content == b'%PDF-'
    assert r.headers['cache-control'] == 'private, no-store'
    assert r.headers['x-content-type-options'] == 'nosniff'
    assert (await client_for_tests.get(download, headers=headers(world, 's2'))).status_code == 404
    for state in ('pending', 'failed'):
        await session_db.execute(update(FileAsset).where(FileAsset.id == asset.id).values(state=state))
        await session_db.commit()
        assert (await client_for_tests.get(download, headers=headers(world))).status_code == 404


@pytest.mark.asyncio
async def test_count_limit_append_and_swap_at_ten(client_for_tests, world):
    file = ('same.pdf', pdf_bytes(), 'application/pdf')
    r = await client_for_tests.patch(route(world, '/student'), headers=headers(world), files=[('files', file)] * 9)
    assert r.status_code == 200, r.text
    assert len(r.json()['files']) == 10
    version = r.json()['version']
    r = await client_for_tests.patch(route(world, '/student'), headers=headers(world), files={'files': file})
    assert r.status_code == 400, r.text
    r = await client_for_tests.put(route(world, f"/files/{world['files'][0].id}"),
                                  headers=headers(world), files={'file': file})
    assert r.status_code == 200 and len(r.json()['files']) == 10 and r.json()['version'] == version + 1


@pytest.mark.asyncio
async def test_saved_byte_sum_is_enforced(client_for_tests, world, session_db):
    r = await client_for_tests.patch(route(world, '/student'), headers=headers(world),
                                    files={'files': ('a.pdf', pdf_bytes(), 'application/pdf')})
    assert r.status_code == 200, r.text
    row = await session_db.get(HomeworkSubmissionFile, r.json()['files'][-1]['id'])
    # Artificial large stored usage, without writing a large test object.
    await session_db.execute(update(HomeworkSubmissionFile).where(HomeworkSubmissionFile.id == row.id).values(source_size=100 * 1024 * 1024))
    await session_db.commit()
    r = await client_for_tests.patch(route(world, '/student'), headers=headers(world),
                                    files={'files': ('b.pdf', pdf_bytes(), 'application/pdf')})
    assert r.status_code == 413
    assert await session_db.scalar(select(func.count()).select_from(FileAsset)) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('name,data', [('fake.pdf', b'MZ exe'), ('broken.pdf', b'%PDF-1.7\n%%EOF'),
                                     ('office.docx', b'PK\x03\x04'), ('page.svg', b'<svg/>'),
                                     ('fake.jpg', b'not an image'), ('empty.pdf', b'')])
async def test_invalid_upload_rolls_back_all_domains(client_for_tests, world, session_db, config_fix, name, data):
    original = set(p for p in config_fix.paths.media.rglob('*') if p.is_file())
    endpoints = [('/lectures', {'lesson_id': world['lessons'][0].id, 'student_user_id': world['accounts']['s1'][0].id}, 'file', 't1'),
                 ('/homeworks', {'lesson_id': world['lessons'][0].id, 'student_user_id': world['accounts']['s1'][0].id, 'title': 'Bad upload'}, 'file', 't1')]
    for url, form, field, actor in endpoints:
        r = await client_for_tests.post(url, headers=headers(world, actor), data=form, files={field: (name, data, 'application/pdf')})
        assert r.status_code == 400, r.text
    r = await client_for_tests.patch(route(world, '/student'), headers=headers(world), files={'files': (name, data, 'application/pdf')})
    assert r.status_code == 400, r.text
    assert await session_db.scalar(select(func.count()).select_from(FileAsset)) == 0
    assert await session_db.scalar(select(func.count()).select_from(Lecture)) == 2
    assert await session_db.scalar(select(func.count()).select_from(Homework)) == 2
    assert set(p for p in config_fix.paths.media.rglob('*') if p.is_file()) == original


@pytest.mark.asyncio
@pytest.mark.parametrize('endpoint', ['lectures', 'homeworks'])
async def test_teacher_commit_failure_compensates_without_touching_old_files(client_for_tests, world, session_db, config_fix, monkeypatch, endpoint):
    original = set(p for p in config_fix.paths.media.rglob('*') if p.is_file())
    async def fail(*args, **kwargs):
        raise RuntimeError('synthetic commit failure')
    with monkeypatch.context() as patch:
        patch.setattr(AsyncSession, 'commit', fail)
        with pytest.raises(RuntimeError, match='synthetic commit failure'):
            await client_for_tests.post('/' + endpoint, headers=headers(world, 't1'),
                data={'lesson_id': world['lessons'][0].id, 'student_user_id': world['accounts']['s1'][0].id, 'title': 'Rollback'},
                files={'file': ('a.pdf', pdf_bytes(), 'application/pdf')})
    assert set(p for p in config_fix.paths.media.rglob('*') if p.is_file()) == original
    assert await session_db.scalar(select(func.count()).select_from(FileAsset)) == 0


@pytest.mark.asyncio
async def test_concurrent_last_slot_serialized(world, client_for_tests, config_fix, session_db):
    import asyncio
    from src.modules.homework_submissions.depends import get_homework_submissions_service
    from src.modules.homework_submissions.models_dto import UpdateSubmissionStudentRequestDTO
    from src.modules.handlers_files.exception import InvalidDocumentFormat
    file = ('a.pdf', pdf_bytes(), 'application/pdf')
    r = await client_for_tests.patch(route(world, '/student'), headers=headers(world), files=[('files', file)] * 8)
    assert r.status_code == 200, r.text
    async def append():
        async with config_fix.db_connection.session_local() as session:
            service = get_homework_submissions_service(session=session, config=config_fix)
            return await service.update_submission_student(world['accounts']['s1'][0].id,
                world['homeworks'][0].id, world['submissions'][0].id, UpdateSubmissionStudentRequestDTO(),
                files=[UploadFile(BytesIO(pdf_bytes()), filename='last.pdf')])
    results = await asyncio.wait_for(asyncio.gather(append(), append(), return_exceptions=True), timeout=30)
    assert sum(isinstance(r, InvalidDocumentFormat) for r in results) == 1, results
    assert sum(not isinstance(r, Exception) for r in results) == 1
    assert await session_db.scalar(select(func.count()).select_from(HomeworkSubmissionFile).where(
        HomeworkSubmissionFile.submission_id == world['submissions'][0].id)) == 10


@pytest.mark.asyncio
@pytest.mark.parametrize('kind', ['jpeg', 'png', 'webp', 'heic'])
async def test_photo_original_remains_identical_pending_d06(client_for_tests, world, session_db, kind):
    from PIL import Image
    import pillow_heif
    pillow_heif.register_heif_opener()
    image = Image.new('RGB', (80, 120), 'white')
    stream = BytesIO()
    image.save(stream, format={'jpeg': 'JPEG', 'png': 'PNG', 'webp': 'WEBP', 'heic': 'HEIF'}[kind])
    source = stream.getvalue()
    r = await client_for_tests.patch(route(world, '/student'), headers=headers(world),
                                    files={'files': (f'photo.{kind}', source, 'application/octet-stream')})
    assert r.status_code == 200, r.text
    row = await session_db.get(HomeworkSubmissionFile, r.json()['files'][-1]['id'])
    assert Path(row.original_file_path).read_bytes() == source
    assert row.original_asset_id != row.download_asset_id
    asset = await session_db.get(FileAsset, row.original_asset_id)
    assert asset.mime.startswith('image/') and asset.size == len(source)
    with Image.open(row.pdf_file_path) as result:
        assert result.format == 'WEBP' and result.size == (80,120)
    download = await client_for_tests.get(route(world, f'/files/{row.id}'), headers=headers(world))
    assert download.headers['content-type'] == 'image/webp'
    assert download.headers['content-disposition'].endswith('.webp')


@pytest.mark.asyncio
async def test_mismatched_extension_and_animation_rejected(client_for_tests, world):
    from PIL import Image
    frames = [Image.new('RGB', (20, 20), color) for color in ('white', 'black')]
    png, animation = BytesIO(), BytesIO()
    frames[0].save(png, format='PNG')
    frames[0].save(animation, format='WEBP', save_all=True, append_images=frames[1:], duration=100)
    for name, source in [('fake.jpg', png.getvalue()), ('animated.webp', animation.getvalue())]:
        r = await client_for_tests.patch(route(world, '/student'), headers=headers(world), files={'files': (name, source, 'image/jpeg')})
        assert r.status_code == 400, r.text


@pytest.mark.asyncio
async def test_approved_original_cleanup_is_post_commit_and_source_usage_retained(
    client_for_tests, world, session_db, config_fix, monkeypatch
):
    from PIL import Image
    from src.modules.course_lifecycle.models import FileDeletion
    from src.modules.course_lifecycle.repository import LifecycleRepository
    from src.modules.course_lifecycle.service import LifecycleService
    # Synthetic-only coverage of the gated branch; dev env remains unapproved.
    monkeypatch.setattr(config_fix, 'photo_originals_approved', True)
    stream = BytesIO(); Image.new('RGB',(80,120),'white').save(stream, 'JPEG')
    source = stream.getvalue()
    r = await client_for_tests.patch(route(world, '/student'), headers=headers(world),
                                    files={'files': ('phone.jpg', source, 'image/jpeg')})
    assert r.status_code == 200, r.text
    row = await session_db.get(HomeworkSubmissionFile, r.json()['files'][-1]['id'])
    assert row.original_asset_id == row.download_asset_id
    assert row.original_file_path == row.pdf_file_path
    assert row.source_size == len(source)
    job = await session_db.scalar(select(FileDeletion).where(FileDeletion.completed.is_(False)))
    assert Path(job.path).read_bytes() == source  # Not deleted before durable commit.
    result = await LifecycleService(LifecycleRepository(session_db), config_fix).cleanup(world['accounts']['admin'][0].id, 100)
    assert result.completed == 1 and not Path(job.path).exists()
    assert Path(row.pdf_file_path).exists()
    assert await session_db.scalar(select(func.count()).select_from(FileAsset)) == 1


@pytest.mark.asyncio
async def test_long_display_name_preserves_extension_and_uuid_paths(client_for_tests,world):
    name='x'*300+'.pdf'
    r=await client_for_tests.patch(route(world,'/student'),headers=headers(world),
        files={'files':(name,pdf_bytes(),'application/pdf')})
    assert r.status_code==200,r.text
    display=r.json()['files'][-1]['original_file_name']
    assert len(display)==200 and display.endswith('.pdf')
    r=await client_for_tests.post('/lectures',headers=headers(world,'t1'),
        data={'lesson_id':world['lessons'][0].id,'student_user_id':world['accounts']['s1'][0].id},
        files={'file':('no-extension',b'data','application/octet-stream')})
    assert r.status_code==400,r.text


@pytest.mark.asyncio
async def test_lost_commit_ack_never_compensates_committed_asset(client_for_tests,world,session_db,monkeypatch):
    data=pdf_bytes('committed before connection error')
    real=AsyncSession.commit
    async def lost_ack(self):
        await real(self)
        raise RuntimeError('synthetic lost commit acknowledgement')
    with monkeypatch.context() as patch:
        patch.setattr(AsyncSession,'commit',lost_ack)
        with pytest.raises(RuntimeError,match='lost commit acknowledgement'):
            await client_for_tests.post('/lectures',headers=headers(world,'t1'),
                data={'lesson_id':world['lessons'][0].id,'student_user_id':world['accounts']['s1'][0].id},
                files={'file':('committed.pdf',data,'application/pdf')})
    row=await session_db.scalar(select(Lecture).where(Lecture.original_file_name=='committed.pdf'))
    assert row is not None and Path(row.pdf_file_path).read_bytes()==data
    url=f"/lectures/{row.id}/file?lesson_id={world['lessons'][0].id}&student_user_id={world['accounts']['s1'][0].id}"
    r=await client_for_tests.get(url,headers=headers(world))
    assert r.status_code==200 and r.content==data
