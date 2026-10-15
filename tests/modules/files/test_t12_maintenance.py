import json
import os
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import func, select, update

from src.modules.files.maintenance import LegacyFileMigration, OrphanReconciliation
from src.modules.files.models import FileAsset
from src.modules.lectures.models import Lecture
from src.modules.course_lifecycle.models import FileDeletion
from src.modules.course_lifecycle.repository import LifecycleRepository
from src.modules.course_lifecycle.service import LifecycleService
from src.tools.synthetic_files import pdf_bytes
from tests.modules.auth.test_t06_permissions import world, auth


@pytest.fixture(autouse=True)
def isolated_maintenance_media(config_fix,monkeypatch,tmp_path):
    from src.core.config.config import PathsConfig
    monkeypatch.setattr(config_fix,'paths',PathsConfig.build(media_root=tmp_path/'maintenance-media'))


async def legacy(world, session, config):
    path = config.paths.lectures / ('old-' + uuid4().hex + '.pdf')
    path.write_bytes(pdf_bytes('legacy copy'))
    await session.execute(update(Lecture).where(Lecture.id==world['lectures'][0].id).values(
        original_file_path=str(path),pdf_file_path=str(path)))
    await session.commit()
    return path


@pytest.mark.asyncio
async def test_migration_manifest_checksum_ids_old_bytes_and_no_global_dedup(
    world, session_db, config_fix, client_for_tests
):
    old = await legacy(world,session_db,config_fix)
    original = old.read_bytes()
    row = await session_db.get(Lecture,world['lectures'][0].id)
    before_updated = row.updated_at
    service = LegacyFileMigration(session_db,config_fix)
    actor_id = world['accounts']['admin'][0].id
    assert (await service.run(actor_id,limit=1)) == {'candidates':1,'migrated':0,'failed':0}
    assert not config_fix.paths.objects.exists()
    result = await service.run(actor_id,apply=True,limit=1)
    assert result == {'candidates':1,'migrated':1,'failed':0}
    session_db.expire_all()
    row = await session_db.get(Lecture,world['lectures'][0].id)
    assert row.updated_at == before_updated
    assert row.original_asset_id == row.download_asset_id and row.original_file_path == row.pdf_file_path
    assert Path(row.pdf_file_path).read_bytes() == original and old.read_bytes() == original
    manifests = list((config_fix.paths.temp/'migration-manifests').glob('*.json'))
    assert len(manifests)==1 and manifests[0].stat().st_mode & 0o777 == 0o600
    manifest = json.loads(manifests[0].read_text())
    assert manifest['retained_paths']==[str(old)] and manifest['state']=='committed'
    assert (await service.run(actor_id,limit=100))['candidates'] >= 1  # Other legacy rows remain, migrated row is absent.
    await session_db.execute(update(Lecture).where(Lecture.id==world['lectures'][1].id).values(
        original_file_path=str(old),pdf_file_path=str(old)))
    await session_db.commit()
    result = await service.run(actor_id,apply=True,limit=1)
    assert result['migrated']==1
    assert await session_db.scalar(select(func.count()).select_from(FileAsset))==2  # Two independent owners/scopes.
    uid=world['accounts']['s1'][0].id
    url=f"/lectures/{world['lectures'][0].id}/file?lesson_id={world['lessons'][0].id}&student_user_id={uid}"
    response=await client_for_tests.get(url,headers=auth(world['accounts']['s1'][1]))
    assert response.status_code==200 and response.content==original


@pytest.mark.asyncio
async def test_orphan_grace_manifest_and_live_references_rechecked(world, session_db, config_fix):
    old=await legacy(world,session_db,config_fix)
    actor=world['accounts']['admin'][0].id
    assert (await LegacyFileMigration(session_db,config_fix).run(actor,apply=True,limit=1))['migrated']==1
    orphan=config_fix.paths.objects/(uuid4().hex+'.pdf');orphan.write_bytes(b'orphan')
    fresh=config_fix.paths.objects/(uuid4().hex+'.pdf');fresh.write_bytes(b'fresh')
    named=config_fix.paths.objects/'not-owned-name.pdf';named.write_bytes(b'never touch')
    for p in [old,orphan,named]:os.utime(p,(1,1))
    reconciler=OrphanReconciliation(session_db,config_fix)
    assert (await reconciler.run())=={'orphan_candidates':1,'queued':0}
    assert orphan.exists() and old.exists()
    assert (await reconciler.run(apply=True))['queued']==1
    assert (await reconciler.run(apply=True))['queued']==0  # No duplicate retry jobs.
    result=await LifecycleService(LifecycleRepository(session_db),config_fix).cleanup(actor,100)
    assert result.completed==1 and not orphan.exists()
    assert fresh.exists() and old.exists() and named.exists()
    # A broken manifest fails closed instead of deleting possible retained sources.
    manifests=config_fix.paths.temp/'migration-manifests'
    (manifests/'broken.json').write_text('{')
    with pytest.raises(ValueError):await reconciler.run(apply=True)


@pytest.mark.asyncio
async def test_migration_commit_failure_compensates_without_losing_sources(world,session_db,config_fix,monkeypatch):
    old=await legacy(world,session_db,config_fix)
    real=session_db.commit
    calls=0
    async def fail_once():
        nonlocal calls
        calls+=1
        if calls==1:raise RuntimeError('synthetic DB commit failure')
        return await real()
    with monkeypatch.context() as patch:
        patch.setattr(session_db,'commit',fail_once)
        result=await LegacyFileMigration(session_db,config_fix).run(world['accounts']['admin'][0].id,apply=True,limit=1)
    assert result['failed']==1 and result['migrated']==0
    assert old.exists() and list(config_fix.paths.objects.iterdir())==[]
    assert await session_db.scalar(select(func.count()).select_from(FileAsset))==0
    row=await session_db.get(Lecture,world['lectures'][0].id)
    assert row.pdf_file_path==str(old) and row.download_asset_id is None


@pytest.mark.asyncio
async def test_legacy_read_switch_and_bad_file_stays_untouched(world,session_db,config_fix,client_for_tests,monkeypatch):
    old=await legacy(world,session_db,config_fix);old.write_bytes(b'%PDF invalid historical synthetic')
    result=await LegacyFileMigration(session_db,config_fix).run(world['accounts']['admin'][0].id,apply=True,limit=1)
    assert result['failed']==1 and old.exists()
    assert await session_db.scalar(select(func.count()).select_from(FileAsset))==0
    uid=world['accounts']['s1'][0].id
    url=f"/lectures/{world['lectures'][0].id}/file?lesson_id={world['lessons'][0].id}&student_user_id={uid}"
    assert (await client_for_tests.get(url,headers=auth(world['accounts']['s1'][1]))).status_code==200
    monkeypatch.setattr(config_fix,'legacy_file_reads',False)
    assert (await client_for_tests.get(url,headers=auth(world['accounts']['s1'][1]))).status_code==404


@pytest.mark.asyncio
async def test_admin_purge_removes_migration_backups_only_after_last_shared_owner(world,session_db,config_fix):
    from src.modules.course_lifecycle.models_dto import PurgeCourseRequest
    old=await legacy(world,session_db,config_fix)
    actor=world['accounts']['admin'][0].id
    await session_db.execute(update(Lecture).where(Lecture.id==world['lectures'][1].id).values(
        original_file_path=str(old),pdf_file_path=str(old)))
    await session_db.commit()
    result=await LegacyFileMigration(session_db,config_fix).run(actor,apply=True,limit=2)
    assert result['migrated']==2
    for index in (0,1):
        service=LifecycleService(LifecycleRepository(session_db),config_fix)
        course=world['courses'][index]
        await service.purge(actor,course.id,PurgeCourseRequest(confirm_course_id=course.id,confirm_name=course.name))
        assert old.exists() == (index==0)


@pytest.mark.asyncio
async def test_explicit_synthetic_opaque_import_preserves_bytes_as_attachment(world,session_db,config_fix,client_for_tests):
    old=await legacy(world,session_db,config_fix)
    payload=b'%PDF historical dummy, not a structurally valid PDF'
    old.write_bytes(payload)
    result=await LegacyFileMigration(session_db,config_fix).run(world['accounts']['admin'][0].id,
        apply=True,limit=1,allow_opaque=True)
    assert result['migrated']==1 and result['failed']==0 and old.read_bytes()==payload
    uid=world['accounts']['s1'][0].id
    url=f"/lectures/{world['lectures'][0].id}/file?lesson_id={world['lessons'][0].id}&student_user_id={uid}"
    response=await client_for_tests.get(url,headers=auth(world['accounts']['s1'][1]))
    assert response.status_code==200 and response.content==payload
    assert response.headers['content-type']=='application/octet-stream'
    assert response.headers['content-disposition'].startswith('attachment;')


@pytest.mark.asyncio
async def test_rollback_window_expiry_verifies_new_copy_before_retiring_duplicate(world,session_db,config_fix):
    from src.modules.files.maintenance import queue_purged_backups
    old=await legacy(world,session_db,config_fix)
    actor=world['accounts']['admin'][0].id
    await LegacyFileMigration(session_db,config_fix).run(actor,apply=True,limit=1)
    manifest=next((config_fix.paths.temp/'migration-manifests').glob('*.json'))
    data=json.loads(manifest.read_text());data['retained_until']='2000-01-01T00:00:00+00:00'
    manifest.write_text(json.dumps(data))
    copied=config_fix.paths.media/data['objects'][0]['key']
    original=copied.read_bytes();copied.write_bytes(b'corrupted')
    with pytest.raises(ValueError):await queue_purged_backups(config_fix,session_db)
    assert old.exists() and await session_db.scalar(select(func.count()).select_from(FileDeletion))==0
    copied.write_bytes(original)
    await queue_purged_backups(config_fix,session_db)
    await LifecycleService(LifecycleRepository(session_db),config_fix).cleanup(actor,100)
    assert not old.exists() and copied.read_bytes()==original
