"""T09: real PostgreSQL locks, preserved attachments, immutable reviewed history."""
import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select, func, update, delete

from src.modules.homework_submissions.models import HomeworkSubmission, HomeworkSubmissionFile, HomeworkSubmissionStatus
from src.modules.homework_submissions.models_dto import UpdateSubmissionStudentRequestDTO
from src.modules.homework_submissions.depends import get_homework_submissions_service
from src.modules.homework_submissions.exception import SubmissionConflict
from src.modules.homework_submissions.repository import HomeworkSubmissionsRepository
from src.modules.course_lifecycle.models import FileDeletion
from src.modules.courses.models import Course
from src.modules.lesson_students.models import LessonStudent
from src.modules.student_courses.models import StudentCourse
from src.modules.homeworks.models import Homework
from tests.modules.auth.test_t06_permissions import world, auth


def route(w, suffix='', index=0):
    return f"/submissions/{w['submissions'][index].id}{suffix}?homework_id={w['homeworks'][index].id}"


def headers(w, actor='s1'):
    return auth(w['accounts'][actor][1])


@pytest.mark.asyncio
async def test_append_same_filename_preserves_ids_bytes_and_download(client_for_tests, world):
    w=world; old=w['files'][0]; content=Path(old.pdf_file_path).read_bytes()
    for payload in (b'%PDF new one', b'%PDF new two'):
        r=await client_for_tests.patch(route(w, '/student'), headers=headers(w),
            files=[('files', ('answer.pdf', payload, 'application/pdf'))])
        assert r.status_code == 200, r.text
        assert r.json()['text_content'] == 'Submission text'
    data=r.json(); assert data['version']==3 and len(data['files'])==3
    assert old.id in [f['id'] for f in data['files']]
    assert Path(old.pdf_file_path).read_bytes()==content
    for f, expected in zip(data['files'], [content,b'%PDF new one',b'%PDF new two']):
        r=await client_for_tests.get(route(w, f"/files/{f['id']}"), headers=headers(w))
        assert r.status_code==200 and r.content==expected


@pytest.mark.asyncio
async def test_submit_edit_idempotence_stale_version_and_late_deadline(client_for_tests, world, session_db):
    w=world
    await session_db.execute(update(Homework).where(Homework.id==w['homeworks'][0].id).values(deadline=datetime.now(UTC)-timedelta(days=2)))
    await session_db.commit()
    r=await client_for_tests.post(route(w,'/submit'),headers=headers(w))
    assert r.status_code==200, r.text
    first=r.json(); assert first['status']=='submitted' and first['submitted_at'].endswith('Z') and first['version']==2
    r=await client_for_tests.post(route(w,'/submit'),headers=headers(w))
    assert r.json()==first
    r=await client_for_tests.patch(route(w,'/student'),headers=headers(w),data={'text_content':'Corrected','expected_version':2})
    assert r.status_code==200 and r.json()['version']==3 and r.json()['submitted_at']==first['submitted_at']
    r=await client_for_tests.patch(route(w,'/student'),headers=headers(w),data={'text_content':'Stale','expected_version':2})
    assert r.status_code==409


@pytest.mark.asyncio
async def test_empty_draft_text_only_and_file_only(client_for_tests, world, session_db):
    w=world
    # Delete the fixture draft, then exercise the public create API.
    assert (await client_for_tests.delete(route(w),headers=headers(w))).status_code==200
    r=await client_for_tests.post(f"/homeworks/{w['homeworks'][0].id}/submissions",headers=headers(w))
    assert r.status_code==201, r.text
    w['submissions'][0]=type('ID',(),{'id':r.json()['id']})()
    assert r.json()['submitted_at'] is None and r.json()['version']==1
    assert (await client_for_tests.post(route(w,'/submit'),headers=headers(w))).status_code==422
    assert (await client_for_tests.patch(route(w,'/student'),headers=headers(w),data={'text_content':'   '})).status_code==200
    assert (await client_for_tests.post(route(w,'/submit'),headers=headers(w))).status_code==422
    assert (await client_for_tests.patch(route(w,'/student'),headers=headers(w),data={'text_content':'Text only'})).status_code==200
    assert (await client_for_tests.post(route(w,'/submit'),headers=headers(w))).json()['status']=='submitted'
    # The other teacher's draft becomes file-only.
    assert (await client_for_tests.patch(route(w,'/student',1),headers=headers(w),data={'text_content':''})).status_code==200
    assert (await client_for_tests.post(route(w,'/submit',1),headers=headers(w))).status_code==200
    assert (await client_for_tests.delete(route(w,f"/files/{w['files'][1].id}",1),headers=headers(w))).status_code==422


@pytest.mark.asyncio
async def test_point_delete_swap_and_durable_cleanup(client_for_tests, world, session_db):
    w=world; old=w['files'][0]; content=Path(old.pdf_file_path).read_bytes()
    r=await client_for_tests.patch(route(w,'/student'),headers=headers(w),files={'files':('second.pdf',b'%PDF second','application/pdf')})
    added=next(f['id'] for f in r.json()['files'] if f['id']!=old.id)
    r=await client_for_tests.put(route(w,f'/files/{old.id}'),headers=headers(w),files={'file':('swap.pdf',b'%PDF swap','application/pdf')})
    assert r.status_code==200, r.text
    ids=[f['id'] for f in r.json()['files']]; assert added in ids and old.id not in ids
    assert Path(old.pdf_file_path).read_bytes()==content  # Unlink is deferred until after durable commit.
    assert await session_db.scalar(select(func.count()).select_from(FileDeletion).where(FileDeletion.path==old.pdf_file_path))==1
    r=await client_for_tests.delete(route(w,f'/files/{added}'),headers=headers(w))
    assert r.status_code==200 and len(r.json()['files'])==1
    assert (await client_for_tests.get(route(w,f'/files/{old.id}'),headers=headers(w))).status_code==404
    assert (await client_for_tests.delete(route(w,f"/files/{w['files'][1].id}"),headers=headers(w))).status_code==404


@pytest.mark.asyncio
@pytest.mark.parametrize('operation',['text','append','remove','swap','delete','teacher','submit','create'])
async def test_checked_immutable_all_paths(client_for_tests, world, session_db, operation):
    w=world; sub=w['submissions'][0]
    await session_db.execute(update(HomeworkSubmission).where(HomeworkSubmission.id==sub.id).values(status=HomeworkSubmissionStatus.CHECKED))
    await session_db.commit()
    h=headers(w); url=route(w)
    if operation=='text': r=await client_for_tests.patch(route(w,'/student'),headers=h,data={'text_content':'Changed'})
    elif operation=='append': r=await client_for_tests.patch(route(w,'/student'),headers=h,files={'files':('f.pdf',b'new','application/pdf')})
    elif operation=='remove': r=await client_for_tests.delete(route(w,f"/files/{w['files'][0].id}"),headers=h)
    elif operation=='swap': r=await client_for_tests.put(route(w,f"/files/{w['files'][0].id}"),headers=h,files={'file':('f.pdf',b'new','application/pdf')})
    elif operation=='delete':
        for actor in ['s1','t1']:
            assert (await client_for_tests.delete(url,headers=headers(w,actor))).status_code==403
        return
    elif operation=='teacher': r=await client_for_tests.patch(route(w,'/teacher'),headers=headers(w,'t1'),json={'grade':0})
    elif operation=='submit': r=await client_for_tests.post(route(w,'/submit'),headers=h)
    else: r=await client_for_tests.post(f"/homeworks/{w['homeworks'][0].id}/submissions",headers=h)
    assert r.status_code==(409 if operation=='create' else 403), r.text
    assert Path(w['files'][0].pdf_file_path).exists()


@pytest.mark.asyncio
@pytest.mark.parametrize('failure',['conversion','insert','commit'])
async def test_upload_swap_rollback_keeps_original(client_for_tests, world, session_db, monkeypatch, config_fix, failure):
    from src.modules.handlers_files.handler_documents import HandlerDocuments
    from sqlalchemy.ext.asyncio import AsyncSession
    w=world; root=config_fix.paths.homework_submissions
    before=set(root.rglob('*')) if root.exists() else set()
    original=Path(w['files'][0].pdf_file_path).read_bytes()
    async def fail(*args,**kwargs): raise RuntimeError('synthetic T09 failure')
    if failure=='conversion':
        real=HandlerDocuments.save_document
        async def partial(self, **kwargs):
            await real(self,**kwargs)
            raise RuntimeError('synthetic T09 failure')
        monkeypatch.setattr(HandlerDocuments,'save_document',partial)
    elif failure=='insert': monkeypatch.setattr(HomeworkSubmissionsRepository,'add_submission_files',fail)
    else: monkeypatch.setattr(AsyncSession,'commit',fail)
    with pytest.raises(RuntimeError,match='synthetic T09'):
        await client_for_tests.put(route(w,f"/files/{w['files'][0].id}"),headers=headers(w),files={'file':('f.pdf',b'%PDF replacement','application/pdf')})
    monkeypatch.undo()
    r=await client_for_tests.get(route(w),headers=headers(w))
    assert r.status_code==200 and r.json()['version']==1 and len(r.json()['files'])==1
    assert Path(w['files'][0].pdf_file_path).read_bytes()==original
    assert {p for p in root.rglob('*') if p.is_file()}=={p for p in before if p.is_file()}
    assert await session_db.scalar(select(func.count()).select_from(FileDeletion))==0


@pytest.mark.asyncio
async def test_historical_attempt_readonly_and_current_blocks_new(client_for_tests, world, session_db):
    w=world
    await session_db.execute(update(HomeworkSubmission).where(HomeworkSubmission.id==w['submissions'][0].id).values(is_working=False))
    new=HomeworkSubmission(homework_id=w['homeworks'][0].id,attempt_number=2,text_content='current')
    session_db.add(new); await session_db.commit()
    r=await client_for_tests.get(f"/homeworks/{w['homeworks'][0].id}/submissions",headers=headers(w))
    assert r.status_code==200 and r.json()['total']==2
    old=next(x for x in r.json()['items'] if not x['is_working'])
    assert old['text_content']=='Submission text' and old['files'][0]['id']==w['files'][0].id
    assert (await client_for_tests.patch(route(w,'/student'),headers=headers(w),data={'text_content':'lost'})).status_code==403
    assert (await client_for_tests.delete(route(w),headers=headers(w,'t1'))).status_code==403
    assert (await client_for_tests.post(f"/homeworks/{w['homeworks'][0].id}/submissions",headers=headers(w))).status_code==409


@pytest.mark.asyncio
async def test_concurrent_create_one_working_answer(config_fix, world, session_db):
    w=world; hid=w['homeworks'][0].id
    await session_db.execute(delete(HomeworkSubmissionFile).where(HomeworkSubmissionFile.submission_id==w['submissions'][0].id))
    await session_db.execute(delete(HomeworkSubmission).where(HomeworkSubmission.id==w['submissions'][0].id))
    await session_db.commit()
    async def run():
        async with config_fix.db_connection.session_local() as session:
            service=get_homework_submissions_service(session=session,config=config_fix)
            try: return await service.create_submission(w['accounts']['s1'][0].id,hid,'answer')
            except SubmissionConflict: return 'conflict'
    results=await asyncio.gather(run(),run())
    assert sum(x=='conflict' for x in results)==1
    assert await session_db.scalar(select(func.count()).select_from(HomeworkSubmission).where(HomeworkSubmission.homework_id==hid,HomeworkSubmission.is_working.is_(True)))==1


@pytest.mark.asyncio
async def test_concurrent_submit_edit_and_append(config_fix, world, client_for_tests):
    from fastapi import UploadFile
    from io import BytesIO
    w=world
    async def run(action):
        async with config_fix.db_connection.session_local() as session:
            service=get_homework_submissions_service(session=session,config=config_fix)
            args=(w['accounts']['s1'][0].id,w['homeworks'][0].id,w['submissions'][0].id)
            if action=='submit': return await service.submit_submission(*args)
            return await service.update_submission_student(*args,UpdateSubmissionStudentRequestDTO(),
                files=[UploadFile(BytesIO(b'%PDF '+action.encode()),filename='same.pdf')])
    await asyncio.gather(run('submit'),run('one'),run('two'))
    r=await client_for_tests.get(route(w),headers=headers(w))
    assert r.json()['version']==4 and r.json()['status']=='submitted' and len(r.json()['files'])==3


@pytest.mark.asyncio
@pytest.mark.parametrize('actor,status',[('t2',404),('s2',404),('t1',403),('admin',403)])
async def test_new_mutations_object_and_role_boundaries(client_for_tests,world,actor,status):
    w=world; h=headers(w,actor)
    for method,suffix,kwargs in [('post','/submit',{}),('delete',f"/files/{w['files'][0].id}",{}),
        ('put',f"/files/{w['files'][0].id}",{'files':{'file':('x.pdf',b'x','application/pdf')}})]:
        r=await getattr(client_for_tests,method)(route(w,suffix),headers=h,**kwargs)
        assert r.status_code==status, r.text


@pytest.mark.asyncio
@pytest.mark.parametrize('condition',['archive','expired'])
async def test_new_mutations_history_readonly(client_for_tests,world,session_db,condition):
    w=world
    if condition=='archive': await session_db.execute(update(Course).where(Course.id==w['courses'][0].id).values(is_deleted=True,deleted_at=datetime.now(UTC)))
    else: await session_db.execute(update(StudentCourse).where(StudentCourse.course_id==w['courses'][0].id).values(expires_at=datetime.now(UTC)))
    await session_db.commit()
    assert (await client_for_tests.post(route(w,'/submit'),headers=headers(w))).status_code==403
    assert (await client_for_tests.delete(route(w,f"/files/{w['files'][0].id}"),headers=headers(w))).status_code==403
    assert (await client_for_tests.get(route(w),headers=headers(w))).status_code==200


@pytest.mark.asyncio
async def test_create_failure_after_flush_rolls_back_answer_and_upload(client_for_tests,world,session_db,monkeypatch,config_fix):
    w=world; hid=w['homeworks'][0].id
    assert (await client_for_tests.delete(route(w),headers=headers(w))).status_code==200
    root=config_fix.paths.homework_submissions
    before={p for p in root.rglob('*') if p.is_file()}
    async def fail(*args,**kwargs): raise RuntimeError('synthetic post-flush failure')
    monkeypatch.setattr(HomeworkSubmissionsRepository,'add_submission_files',fail)
    with pytest.raises(RuntimeError,match='post-flush'):
        await client_for_tests.post(f'/homeworks/{hid}/submissions',headers=headers(w),
            files={'files':('new.pdf',b'%PDF new','application/pdf')})
    assert await session_db.scalar(select(func.count()).select_from(HomeworkSubmission).where(HomeworkSubmission.homework_id==hid))==0
    assert {p for p in root.rglob('*') if p.is_file()}==before


@pytest.mark.asyncio
async def test_failed_second_append_keeps_prior_files_and_text(client_for_tests,world,config_fix):
    w=world; root=config_fix.paths.homework_submissions
    before={p for p in root.rglob('*') if p.is_file()}
    r=await client_for_tests.patch(route(w,'/student'),headers=headers(w),data={'text_content':'rollback text'},
        files=[('files',('same.pdf',b'%PDF valid','application/pdf')),('files',('bad.exe',b'bad','application/octet-stream'))])
    assert r.status_code==400, r.text
    r=await client_for_tests.get(route(w),headers=headers(w))
    assert r.json()['text_content']=='Submission text' and r.json()['version']==1 and len(r.json()['files'])==1
    assert {p for p in root.rglob('*') if p.is_file()}==before


@pytest.mark.asyncio
async def test_mutation_response_keeps_gap_file_scope(client_for_tests,world,session_db):
    w=world; cut=datetime.now(UTC)-timedelta(seconds=5)
    for model,key in [(LessonStudent,'recipients'),(Homework,'homeworks'),(HomeworkSubmission,'submissions'),(HomeworkSubmissionFile,'files')]:
        await session_db.execute(update(model).where(model.id==w[key][0].id).values(created_at=cut-timedelta(seconds=1)))
    hidden=HomeworkSubmissionFile(submission_id=w['submissions'][0].id,pdf_file_path=str(w['avatar']),
        pdf_file_name='hidden-gap.pdf',created_at=cut+timedelta(seconds=1))
    session_db.add(hidden)
    await session_db.execute(update(StudentCourse).where(StudentCourse.course_id==w['courses'][0].id).values(expires_at=cut))
    await session_db.commit(); hidden_id=hidden.id
    r=await client_for_tests.post(f"/courses/{w['courses'][0].id}/students",headers=headers(w,'t1'),
        json={'student_user_id':w['accounts']['s1'][0].id})
    assert r.status_code==201,r.text
    for method,suffix,kwargs in [('patch','/student',{'data':{'text_content':'visible change'}}),('post','/submit',{})]:
        r=await getattr(client_for_tests,method)(route(w,suffix),headers=headers(w),**kwargs)
        assert r.status_code==200,r.text
        assert hidden_id not in [f['id'] for f in r.json()['files']]
    assert (await client_for_tests.delete(route(w,f'/files/{hidden_id}'),headers=headers(w))).status_code==404
    assert (await client_for_tests.get(route(w,f'/files/{hidden_id}'),headers=headers(w))).status_code==404
    assert (await client_for_tests.delete(route(w),headers=headers(w))).status_code==403
