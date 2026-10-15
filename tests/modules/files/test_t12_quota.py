import asyncio
from io import BytesIO

import pytest
from fastapi import UploadFile
from sqlalchemy import select, update

from src.modules.files.models import FileAsset
from src.modules.homework_submissions.models import HomeworkSubmissionFile
from src.modules.homework_submissions.models_dto import UpdateSubmissionStudentRequestDTO
from src.modules.homework_submissions.depends import get_homework_submissions_service
from src.modules.handlers_files.exception import FileTooLarge
from src.tools.synthetic_files import pdf_bytes
from tests.modules.auth.test_t06_permissions import world, auth
from tests.modules.homework_submissions.test_t09_lifecycle import route, headers


@pytest.mark.asyncio
async def test_quota_report_private_admin_override_warning_and_existing_download(client_for_tests,world,session_db):
    uid=world['accounts']['s1'][0].id
    url=f'/users/{uid}/storage';limit=f'/admin/users/{uid}/storage-quota'
    r=await client_for_tests.get(url,headers=headers(world))
    assert r.status_code==200 and r.json()['limit_bytes']==1024**3
    assert (await client_for_tests.get(url,headers=headers(world,'s2'))).status_code==403
    assert (await client_for_tests.patch(limit,headers=headers(world,'t1'),json={'limit_bytes':20*1024**2})).status_code==403
    assert (await client_for_tests.patch(limit,headers=headers(world,'admin'),json={'limit_bytes':True})).status_code==422
    r=await client_for_tests.patch(limit,headers=headers(world,'admin'),json={'limit_bytes':20*1024**2})
    assert r.status_code==200,r.text
    data=pdf_bytes('quota')
    r=await client_for_tests.patch(route(world,'/student'),headers=headers(world),files={'files':('a.pdf',data,'application/pdf')})
    assert r.status_code==200,r.text
    file_id=r.json()['files'][-1]['id'];row=await session_db.get(HomeworkSubmissionFile,file_id)
    # Simulate a nearly full budget without generating a 20 MiB fixture object.
    await session_db.execute(update(FileAsset).where(FileAsset.id==row.original_asset_id).values(size=20*1024**2-len(data)+1))
    await session_db.commit()
    r=await client_for_tests.get(url,headers=headers(world))
    assert r.json()['warning']=='critical' and r.json()['courses'][0]['course_id']==world['courses'][0].id
    assert (await client_for_tests.patch(route(world,'/student'),headers=headers(world),files={'files':('b.pdf',data,'application/pdf')})).status_code==413
    assert (await client_for_tests.get(route(world,f'/files/{file_id}'),headers=headers(world))).content==data
    await client_for_tests.patch(limit,headers=headers(world,'admin'),json={'limit_bytes':40*1024**2})
    assert (await client_for_tests.patch(route(world,'/student'),headers=headers(world),files={'files':('b.pdf',data,'application/pdf')})).status_code==200


@pytest.mark.asyncio
async def test_global_student_budget_serializes_parallel_different_courses(client_for_tests,world,session_db,config_fix):
    data=pdf_bytes('last quota slot');uid=world['accounts']['s1'][0].id
    r=await client_for_tests.patch(route(world,'/student'),headers=headers(world),files={'files':('a.pdf',data,'application/pdf')})
    assert r.status_code==200
    row=await session_db.get(HomeworkSubmissionFile,r.json()['files'][-1]['id'])
    from src.modules.users.models import User
    await session_db.execute(update(User).where(User.id==uid).values(file_quota_bytes=20*1024**2))
    await session_db.execute(update(FileAsset).where(FileAsset.id==row.original_asset_id).values(size=20*1024**2-len(data)))
    await session_db.commit()
    async def append(index):
        async with config_fix.db_connection.session_local() as session:
            return await get_homework_submissions_service(session=session,config=config_fix).update_submission_student(
                uid,world['homeworks'][index].id,world['submissions'][index].id,UpdateSubmissionStudentRequestDTO(),
                files=[UploadFile(BytesIO(data),filename='last.pdf')])
    results=await asyncio.wait_for(asyncio.gather(append(0),append(1),return_exceptions=True),timeout=30)
    assert sum(isinstance(r,FileTooLarge) for r in results)==1,results
    assert sum(not isinstance(r,Exception) for r in results)==1
