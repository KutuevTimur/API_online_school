"""Atomic teacher feedback attachments, scoped reads and immutable results."""
from pathlib import Path
import pytest
from sqlalchemy import select, func
from src.tools.synthetic_files import pdf_bytes
from src.modules.homework_submissions.models import HomeworkSubmissionFile, HomeworkSubmission
from src.modules.files.models import FileAsset
from tests.modules.auth.test_t06_permissions import world
from tests.modules.homework_submissions.test_t09_lifecycle import route, headers

async def submitted(client, w):
    r = await client.post(route(w, '/submit'), headers=headers(w))
    assert r.status_code == 200
    return r.json()['version']

@pytest.mark.asyncio
async def test_review_files_separate_scoped_and_immutable(client_for_tests, world, session_db):
    w = world; c = client_for_tests
    version = await submitted(c, w)
    payload = pdf_bytes('Teacher feedback')
    r = await c.patch(route(w, '/review'), headers=headers(w, 't1'),
        data={'expected_version': str(version), 'grade': '0', 'teacher_comment': 'Check the signs'},
        files=[('files', ('feedback.pdf', payload, 'application/pdf')), ('files', ('more.pdf', payload, 'application/pdf'))])
    assert r.status_code == 200, r.text
    body = r.json()
    assert body['grade'] == 0 and body['status'] == 'checked'
    assert len(body['files']) == 1 and len(body['review_files']) == 2
    for file in body['review_files']:
        url = file['file']['download_url']
        for actor in ('s1', 't1'):
            read = await c.get(url, headers=headers(w, actor))
            assert read.status_code == 200 and read.content == payload
        assert (await c.get(url, headers=headers(w, 't2'))).status_code == 404
        assert (await c.get(url, headers=headers(w, 's2'))).status_code == 404
        row = await session_db.get(HomeworkSubmissionFile, file['id'])
        assert row.purpose == 'review'
        asset = await session_db.get(FileAsset, row.download_asset_id)
        assert asset.uploader_user_id == w['accounts']['t1'][0].id
        assert (await c.delete(route(w, f"/files/{file['id']}"), headers=headers(w),
                              params={'homework_id': w['homeworks'][0].id, 'expected_version': body['version']})).status_code == 403
    read = await c.get(route(w), headers=headers(w))
    assert read.json() == body
    assert (await c.patch(route(w, '/teacher'), headers=headers(w, 't1'),
        json={'expected_version': body['version'], 'grade': 5})).status_code == 403

@pytest.mark.asyncio
@pytest.mark.parametrize('failure', ['invalid_file', 'stale', 'eleven'])
async def test_failed_review_rolls_back_files_and_result(client_for_tests, world, session_db, config_fix, failure):
    c=client_for_tests; w=world
    version=await submitted(c,w)
    before={p for p in config_fix.paths.media.rglob('*') if p.is_file()}
    count=await session_db.scalar(select(func.count()).select_from(FileAsset))
    files=[('files', ('valid.pdf', pdf_bytes(), 'application/pdf'))]
    if failure == 'invalid_file': files.append(('files', ('bad.pdf', b'broken', 'application/pdf')))
    if failure == 'eleven': files=files*11
    r=await c.patch(route(w,'/review'),headers=headers(w,'t1'),
        data={'expected_version':str(version-1 if failure=='stale' else version),'grade':'5'},files=files)
    assert r.status_code == (409 if failure=='stale' else 400),r.text
    data=(await c.get(route(w),headers=headers(w))).json()
    assert data['status']=='submitted' and data['version']==version and not data['review_files']
    assert await session_db.scalar(select(func.count()).select_from(FileAsset))==count
    assert {p for p in config_fix.paths.media.rglob('*') if p.is_file()}==before

@pytest.mark.asyncio
@pytest.mark.parametrize('grade', ['5.0', 'true', '6', '-1'])
async def test_review_multipart_requires_exact_integer_grade(client_for_tests,world,grade):
    version=await submitted(client_for_tests,world)
    r=await client_for_tests.patch(route(world,'/review'),headers=headers(world,'t1'),
        data={'expected_version':str(version),'grade':grade},files={'files':('a.pdf',pdf_bytes(),'application/pdf')})
    assert r.status_code==422
