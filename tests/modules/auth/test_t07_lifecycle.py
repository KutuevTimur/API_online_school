"""D02: archive/read-only, historical publication grants and durable purge."""
from datetime import datetime, UTC, timedelta
from pathlib import Path
import pytest
from sqlalchemy import select, update, func
from src.modules.courses.models import Course
from src.modules.lessons.models import Lesson
from src.modules.lesson_students.models import LessonStudent
from src.modules.student_courses.models import StudentCourse
from src.modules.lectures.models import Lecture
from src.modules.homeworks.models import Homework
from src.modules.homework_submissions.models import HomeworkSubmission, HomeworkSubmissionFile
from src.modules.course_lifecycle.models import FileDeletion, LifecycleAudit, EnrollmentGap
from tests.modules.auth.test_t06_permissions import world, auth, urls


@pytest.mark.asyncio
async def test_archive_preserves_chain_read_download_and_blocks_writes(client_for_tests, world, session_db):
    w=world; c=w['courses'][0].id; l=w['lessons'][0].id; h=w['homeworks'][0].id
    teacher=auth(w['accounts']['t1'][1]); student=auth(w['accounts']['s1'][1])
    sub=w['submissions'][0].id; uid=w['accounts']['s1'][0].id
    for _ in range(2):
        r=await client_for_tests.delete(f'/courses/{c}',headers=teacher)
        assert r.status_code==200,r.text
    assert await session_db.get(Lesson,l)
    assert await session_db.get(Homework,h)
    assert await session_db.get(HomeworkSubmission,sub)
    for url in urls(w,0):
        if not url.endswith('/students'):
            r=await client_for_tests.get(url,headers=student)
            assert r.status_code==200,(url,r.text)
    requests=[('patch',f'/courses/{c}',{'name':'blocked'}),
              ('patch',f'/lessons/{l}',{'title':'blocked'}),
              ('delete',f'/lessons/{l}',None),
              ('delete',f'/homeworks/{h}?lesson_id={l}&student_user_id={uid}',None),
              ('delete',f'/submissions/{sub}?homework_id={h}',None)]
    for method,url,data in requests:
        kwargs={'json':data} if data else {}
        r=await client_for_tests.request(method,url,headers=teacher,**kwargs)
        assert r.status_code==403,(method,url,r.text)
    r=await client_for_tests.post(f'/homeworks/{h}/submissions',headers=student,data={'text_content':'blocked'})
    assert r.status_code==403,r.text
    # Other teacher/course continues to be writable.
    r=await client_for_tests.patch(f'/lessons/{w["lessons"][1].id}',headers=auth(w['accounts']['t2'][1]),json={'title':'allowed'})
    assert r.status_code==200,r.text


@pytest.mark.asyncio
async def test_restore_admin_only_and_does_not_revive_lesson(client_for_tests,world,session_db):
    w=world; c=w['courses'][0].id; l=w['lessons'][0].id
    t=auth(w['accounts']['t1'][1]); a=auth(w['accounts']['admin'][1])
    for _ in range(2):
        assert (await client_for_tests.delete(f'/lessons/{l}',headers=t)).status_code==200
    assert (await client_for_tests.delete(f'/courses/{c}',headers=t)).status_code==200
    assert (await client_for_tests.post(f'/courses/{c}/restore',headers=t)).status_code==403
    for _ in range(2):
        assert (await client_for_tests.post(f'/courses/{c}/restore',headers=a)).status_code==200
    session_db.expire_all()
    assert (await session_db.get(Lesson,l)).is_deleted
    assert (await client_for_tests.patch(f'/lessons/{l}',headers=t,json={'title':'no'})).status_code==403
    assert (await client_for_tests.post(f'/lessons/{l}/restore',headers=a)).status_code==200
    assert (await client_for_tests.patch(f'/lessons/{l}',headers=t,json={'title':'yes'})).status_code==200


@pytest.mark.asyncio
@pytest.mark.parametrize('expiry',[False,True])
async def test_cutoff_late_materials_lists_files_and_reenrollment(client_for_tests,world,session_db,expiry):
    w=world; c=w['courses'][0].id; l=w['lessons'][0].id; ls=w['recipients'][0].id
    uid=w['accounts']['s1'][0].id; t=auth(w['accounts']['t1'][1]); s=auth(w['accounts']['s1'][1])
    # Explicit timestamps keep boundary assertions independent of machine speed.
    cut=datetime.now(UTC)-timedelta(seconds=5)
    for model,ident in [(LessonStudent,ls),(Homework,w['homeworks'][0].id),(Lecture,w['lectures'][0].id)]:
        await session_db.execute(update(model).where(model.id==ident).values(created_at=cut-timedelta(seconds=2)))
    enrollment=await session_db.scalar(select(StudentCourse).where(StudentCourse.course_id==c))
    if expiry:
        enrollment.expires_at=cut
    else:
        enrollment.is_deleted=True; enrollment.deleted_at=cut; enrollment.access_ended_at=cut
    late=Lecture(lesson_student_id=ls,original_file_path='unused',original_file_name='late.pdf',original_file_type='pdf',
                 pdf_file_path=str(w['avatar']),pdf_file_name='late.pdf',created_at=cut+timedelta(seconds=1))
    session_db.add(late); await session_db.commit(); late_id=late.id
    q=f'lesson_id={l}&student_user_id={uid}'
    r=await client_for_tests.get(f'/lectures?{q}',headers=s)
    assert r.status_code==200 and r.json()['total']==1,r.text
    assert (await client_for_tests.get(f'/lectures/{late_id}/file?{q}',headers=s)).status_code==404
    assert (await client_for_tests.get(f'/courses/{c}',headers=s)).status_code==200
    assert (await client_for_tests.post(f'/homeworks/{w["homeworks"][0].id}/submissions',headers=s,data={'text_content':'no'})).status_code==403
    assert (await client_for_tests.get(f'/courses/{w["courses"][1].id}',headers=s)).status_code==200
    # Reenrollment restores participation, but does not grant publications from the gap.
    r=await client_for_tests.post(f'/courses/{c}/students',headers=t,json={'student_user_id':uid})
    assert r.status_code==201,r.text
    assert (await client_for_tests.get(f'/lectures/{late_id}/file?{q}',headers=s)).status_code==404
    assert await session_db.scalar(select(func.count()).select_from(EnrollmentGap))==1


@pytest.mark.asyncio
async def test_explicit_history_revocation_and_teacher_history(client_for_tests,world):
    w=world; c=w['courses'][0].id; uid=w['accounts']['s1'][0].id
    path=f'/courses/{c}/students/{uid}/history-access'
    assert (await client_for_tests.patch(path,headers=auth(w['accounts']['t1'][1]),json={'revoked':True})).status_code==403
    for revoked,status in [(True,404),(False,200)]:
        assert (await client_for_tests.patch(path,headers=auth(w['accounts']['admin'][1]),json={'revoked':revoked})).status_code==204
        for url in [f'/courses/{c}',f'/lessons/{w["lessons"][0].id}',urls(w,0)[4],urls(w,0)[-1]]:
            assert (await client_for_tests.get(url,headers=auth(w['accounts']['s1'][1]))).status_code==status
        assert (await client_for_tests.get(f'/courses/{c}',headers=auth(w['accounts']['t1'][1]))).status_code==200


@pytest.mark.asyncio
async def test_purge_confirmation_roles_and_shared_files(client_for_tests,world,session_db,path_builder_fixture):
    w=world; c=w['courses'][0].id
    path=path_builder_fixture.get_lecture_pdf(w['lectures'][0].id,'shared'); path.write_bytes(b'synthetic')
    await session_db.execute(update(Lecture).values(original_file_path=str(path),pdf_file_path=str(path)))
    await session_db.commit()
    payload={'confirm_course_id':c,'confirm_name':w['courses'][0].name}
    assert (await client_for_tests.post(f'/courses/{c}/purge',headers=auth(w['accounts']['t1'][1]),json=payload)).status_code==403
    a=auth(w['accounts']['admin'][1])
    bad={**payload,'confirm_name':'wrong'}
    assert (await client_for_tests.post(f'/courses/{c}/purge',headers=a,json=bad)).status_code==400
    assert await session_db.get(Course,c)
    r=await client_for_tests.post(f'/courses/{c}/purge',headers=a,json=payload)
    assert r.status_code==200,r.text
    session_db.expire_all()
    assert await session_db.get(Course,c) is None
    assert await session_db.get(Lesson,w['lessons'][0].id) is None
    assert await session_db.get(Course,w['courses'][1].id)
    assert path.is_file()  # still referenced by second teacher
    assert await session_db.scalar(select(func.count()).select_from(LifecycleAudit).where(LifecycleAudit.action=='purge'))==1
    # Second purge removes last reference; retry then removes shared object safely.
    c2=w['courses'][1].id
    r=await client_for_tests.post(f'/courses/{c2}/purge',headers=a,json={'confirm_course_id':c2,'confirm_name':w['courses'][1].name})
    assert r.status_code==200,r.text
    assert not path.exists()
    assert (await client_for_tests.post('/admin/file-deletions/retry',headers=a)).status_code==200


@pytest.mark.asyncio
async def test_purge_rollback_keeps_files_and_queue_atomic(world,session_db,config_fix,path_builder_fixture,monkeypatch):
    from src.modules.course_lifecycle.repository import LifecycleRepository
    from src.modules.course_lifecycle.service import LifecycleService
    from src.modules.course_lifecycle.models_dto import PurgeCourseRequest
    w=world; c=w['courses'][0].id
    path=path_builder_fixture.get_lecture_pdf(w['lectures'][0].id,'keep'); path.write_bytes(b'keep')
    await session_db.execute(update(Lecture).where(Lecture.id==w['lectures'][0].id).values(pdf_file_path=str(path)))
    await session_db.commit()
    repo=LifecycleRepository(session_db); original=repo.purge
    async def fail(course_id):
        await original(course_id)
        raise RuntimeError('injected before commit')
    monkeypatch.setattr(repo,'purge',fail)
    with pytest.raises(RuntimeError):
        await LifecycleService(repo,config_fix).purge(w['accounts']['admin'][0].id,c,
            PurgeCourseRequest(confirm_course_id=c,confirm_name=w['courses'][0].name))
    assert await session_db.get(Course,c)
    assert path.read_bytes()==b'keep'
    assert await session_db.scalar(select(func.count()).select_from(FileDeletion))==0


@pytest.mark.asyncio
async def test_cleanup_failure_restart_retry_and_path_boundary(world,session_db,config_fix,path_builder_fixture,monkeypatch,tmp_path):
    from src.modules.course_lifecycle.repository import LifecycleRepository
    from src.modules.course_lifecycle.service import LifecycleService
    a=world['accounts']['admin'][0].id
    path=path_builder_fixture.get_lecture_pdf(999,'retry'); path.write_bytes(b'retry')
    outside=tmp_path/'outside'; outside.write_bytes(b'outside')
    session_db.add_all([FileDeletion(path=str(path)),FileDeletion(path=str(outside))]); await session_db.commit()
    from src.modules.storage.service import LocalStorage
    original=LocalStorage.delete
    async def fail(self,key):
        if self.root / key == path: raise OSError('injected')
        return await original(self,key)
    with monkeypatch.context() as patch:
        patch.setattr(LocalStorage,'delete',fail)
        result=await LifecycleService(LifecycleRepository(session_db),config_fix).cleanup(a,100)
        assert result.failed==2 and path.exists()
    # New service instance represents a restarted worker; persisted jobs remain.
    result=await LifecycleService(LifecycleRepository(session_db),config_fix).cleanup(a,100)
    assert result.completed==1 and result.failed==1
    assert not path.exists() and outside.read_bytes()==b'outside'


@pytest.mark.asyncio
async def test_cutoff_nested_submission_files_and_direct_ids(client_for_tests,world,session_db):
    w=world; cut=datetime.now(UTC)-timedelta(seconds=5)
    enrollment=await session_db.scalar(select(StudentCourse).where(StudentCourse.course_id==w['courses'][0].id))
    enrollment.expires_at=cut
    for model,key in [(LessonStudent,'recipients'),(Homework,'homeworks'),(HomeworkSubmission,'submissions'),(HomeworkSubmissionFile,'files')]:
        await session_db.execute(update(model).where(model.id==w[key][0].id).values(created_at=cut-timedelta(seconds=1)))
    late=HomeworkSubmissionFile(submission_id=w['submissions'][0].id,pdf_file_path=str(w['avatar']),created_at=cut+timedelta(seconds=1))
    # T09: preserve the cutoff fixture as an historical, read-only attempt.
    await session_db.execute(update(HomeworkSubmission).where(HomeworkSubmission.id==w['submissions'][0].id).values(is_working=False))
    late_sub=HomeworkSubmission(homework_id=w['homeworks'][0].id,attempt_number=2,created_at=cut+timedelta(seconds=1))
    session_db.add_all([late,late_sub]); await session_db.commit()
    h=w['homeworks'][0].id; sub=w['submissions'][0].id
    headers=auth(w['accounts']['s1'][1])
    r=await client_for_tests.get(f'/submissions/{sub}?homework_id={h}',headers=headers)
    assert r.status_code==200,r.text
    assert [f['id'] for f in r.json()['files']]==[w['files'][0].id]
    assert (await client_for_tests.get(f'/submissions/{sub}/files/{late.id}?homework_id={h}',headers=headers)).status_code==404
    assert (await client_for_tests.get(f'/submissions/{late_sub.id}?homework_id={h}',headers=headers)).status_code==404
    r=await client_for_tests.get(f'/homeworks/{h}/submissions?offset=99',headers=headers)
    assert r.status_code==200 and r.json()['total']==1 and not r.json()['items'],r.text


@pytest.mark.asyncio
async def test_unenroll_preserves_reading_and_restore_does_not_reenroll(client_for_tests,world,session_db):
    w=world;c=w['courses'][0].id;s=auth(w['accounts']['s1'][1]);t=auth(w['accounts']['t1'][1]);a=auth(w['accounts']['admin'][1])
    assert (await client_for_tests.delete(f'/courses/{c}/students/me',headers=s)).status_code==204
    assert (await client_for_tests.delete(f'/courses/{c}',headers=t)).status_code==200
    assert (await client_for_tests.post(f'/courses/{c}/restore',headers=a)).status_code==200
    session_db.expire_all()
    enrollment=await session_db.scalar(select(StudentCourse).where(StudentCourse.course_id==c))
    assert enrollment.is_deleted and enrollment.access_ended_at
    assert (await client_for_tests.get(f'/courses/{c}',headers=s)).status_code==200
    h=w['homeworks'][0].id; sub=w['submissions'][0].id
    assert (await client_for_tests.patch(f'/submissions/{sub}/teacher?homework_id={h}',headers=t,json={'grade':5,'expected_version':1})).status_code==403
    assert (await client_for_tests.patch(f'/submissions/{sub}/student?homework_id={h}',headers=s,data={'text_content':'no'})).status_code==403
    assert (await client_for_tests.delete(f'/submissions/{sub}?homework_id={h}',headers=s)).status_code==403


@pytest.mark.asyncio
@pytest.mark.parametrize('grant_offset',[-1,0,1])
@pytest.mark.parametrize('publication_offset',[-1,0,1])
async def test_inclusive_cutoff_before_pagination_and_my_materials(client_for_tests,world,session_db,grant_offset,publication_offset):
    w=world; cut=datetime.now(UTC)-timedelta(seconds=10)
    c=w['courses'][0].id; l=w['lessons'][0].id; lecture=w['lectures'][0].id; uid=w['accounts']['s1'][0].id
    await session_db.execute(update(StudentCourse).where(StudentCourse.course_id==c).values(expires_at=cut))
    await session_db.execute(update(LessonStudent).where(LessonStudent.id==w['recipients'][0].id).values(created_at=cut+timedelta(seconds=grant_offset)))
    await session_db.execute(update(Lecture).where(Lecture.id==lecture).values(created_at=cut+timedelta(seconds=publication_offset)))
    await session_db.commit()
    headers=auth(w['accounts']['s1'][1]); expected=grant_offset<=0 and publication_offset<=0
    q=f'lesson_id={l}&student_user_id={uid}'
    r=await client_for_tests.get(f'/lectures/{lecture}/file?{q}',headers=headers)
    assert r.status_code==(200 if expected else 404),r.text
    r=await client_for_tests.get(f'/lectures?{q}&offset=99',headers=headers)
    if grant_offset>0:
        assert r.status_code==404,r.text
    else:
        assert r.status_code==200 and r.json()['total']==int(expected) and not r.json()['items'],r.text
    r=await client_for_tests.get('/lectures/my',headers=headers)
    assert r.status_code==200,r.text
    assert (lecture in {x['id'] for x in r.json()['items']})==expected


@pytest.mark.asyncio
async def test_archive_serializes_queued_write(world,config_fix):
    import asyncio
    from src.modules.check_permission.service import ObjectPermissionService
    from src.modules.check_permission.exception import PermissionErrorService
    w=world; c=w['courses'][0].id; l=w['lessons'][0].id; teacher=w['accounts']['t1'][0].id
    factory=config_fix.db_connection.session_local
    async with factory() as first, factory() as second:
        permissions=ObjectPermissionService(first)
        assert await permissions.repo.writable_course(c)
        course=await first.get(Course,c); course.soft_delete(); await first.flush()
        started=asyncio.Event()
        async def waiting_writer():
            started.set()
            try:
                await ObjectPermissionService(second).require(teacher,'lesson',l,write=True)
            finally:
                await second.rollback()
        task=asyncio.create_task(waiting_writer())
        await started.wait()
        await asyncio.sleep(0.05)
        await first.commit()
        with pytest.raises(PermissionErrorService):
            await asyncio.wait_for(task,5)


@pytest.mark.asyncio
async def test_committed_purge_queue_survives_cleanup_crash(world,session_db,config_fix,path_builder_fixture,monkeypatch):
    from src.modules.course_lifecycle.repository import LifecycleRepository
    from src.modules.course_lifecycle.service import LifecycleService
    from src.modules.course_lifecycle.models_dto import PurgeCourseRequest
    w=world;c=w['courses'][0].id;actor=w['accounts']['admin'][0].id
    path=path_builder_fixture.get_lecture_pdf(w['lectures'][0].id,'durable');path.write_bytes(b'durable')
    await session_db.execute(update(Lecture).where(Lecture.id==w['lectures'][0].id).values(pdf_file_path=str(path)))
    await session_db.commit()
    service=LifecycleService(LifecycleRepository(session_db),config_fix)
    async def crash(*args): raise RuntimeError('worker interrupted after domain commit')
    monkeypatch.setattr(service,'cleanup',crash)
    with pytest.raises(RuntimeError):
        await service.purge(actor,c,PurgeCourseRequest(confirm_course_id=c,confirm_name=w['courses'][0].name))
    session_db.expire_all()
    assert await session_db.get(Course,c) is None
    assert path.exists()
    assert await session_db.scalar(select(func.count()).select_from(FileDeletion).where(FileDeletion.completed.is_(False)))>0
    await LifecycleService(LifecycleRepository(session_db),config_fix).cleanup(actor,100)
    assert not path.exists()


@pytest.mark.asyncio
async def test_ended_teacher_link_keeps_history_and_relink_preserves_gap(client_for_tests,world,session_db):
    from src.modules.teacher_students.models import TeacherStudent
    w=world; cut=datetime.now(UTC)-timedelta(seconds=5)
    ls=w['recipients'][0].id; lecture=w['lectures'][0].id
    await session_db.execute(update(TeacherStudent).where(TeacherStudent.teacher_id==w['teachers'][0].id).values(started_at=cut-timedelta(seconds=10),ended_at=cut))
    await session_db.execute(update(LessonStudent).where(LessonStudent.id==ls).values(created_at=cut-timedelta(seconds=1)))
    await session_db.execute(update(Homework).where(Homework.id==w['homeworks'][0].id).values(created_at=cut-timedelta(seconds=1)))
    await session_db.execute(update(Lecture).where(Lecture.id==lecture).values(created_at=cut+timedelta(seconds=1)))
    await session_db.commit()
    s=auth(w['accounts']['s1'][1]); t=auth(w['accounts']['t1'][1]); a=auth(w['accounts']['admin'][1])
    url=f'/lectures/{lecture}/file?lesson_id={w["lessons"][0].id}&student_user_id={w["accounts"]["s1"][0].id}'
    assert (await client_for_tests.get(url,headers=s)).status_code==404
    assert (await client_for_tests.get(url,headers=t)).status_code==200
    assert (await client_for_tests.patch(f'/lessons/{w["lessons"][0].id}',headers=t,json={'title':'blocked'})).status_code==403
    assert (await client_for_tests.get(f'/courses/{w["courses"][1].id}',headers=s)).status_code==200
    r=await client_for_tests.post('/teacher_students',headers=a,json={'teacher_user_id':w['accounts']['t1'][0].id,'student_user_id':w['accounts']['s1'][0].id})
    assert r.status_code==200,r.text
    assert (await client_for_tests.get(url,headers=s)).status_code==404
    assert (await client_for_tests.patch(f'/lessons/{w["lessons"][0].id}',headers=t,json={'title':'allowed'})).status_code==200


@pytest.mark.asyncio
async def test_reenrolled_student_cannot_mutate_hidden_gap_submission(client_for_tests,world,session_db):
    w=world;cut=datetime.now(UTC)-timedelta(seconds=5);c=w['courses'][0].id;h=w['homeworks'][0].id;sub=w['submissions'][0].id
    for model,key in [(LessonStudent,'recipients'),(Homework,'homeworks')]:
        await session_db.execute(update(model).where(model.id==w[key][0].id).values(created_at=cut-timedelta(seconds=1)))
    await session_db.execute(update(StudentCourse).where(StudentCourse.course_id==c).values(expires_at=cut))
    await session_db.execute(update(HomeworkSubmission).where(HomeworkSubmission.id==sub).values(created_at=cut+timedelta(seconds=1)))
    await session_db.commit()
    r=await client_for_tests.post(f'/courses/{c}/students',headers=auth(w['accounts']['t1'][1]),json={'student_user_id':w['accounts']['s1'][0].id})
    assert r.status_code==201,r.text
    s=auth(w['accounts']['s1'][1])
    assert (await client_for_tests.patch(f'/submissions/{sub}/student?homework_id={h}',headers=s,data={'text_content':'hidden'})).status_code==404
    assert (await client_for_tests.delete(f'/submissions/{sub}?homework_id={h}',headers=s)).status_code==404


@pytest.mark.asyncio
async def test_detached_recipient_does_not_block_another_personal_recipient(client_for_tests,world,session_db):
    w=world;c=w['courses'][0].id;l=w['lessons'][0].id;other=w['students'][1].id
    session_db.add(StudentCourse(course_id=c,student_id=other))
    ls=LessonStudent(lesson_id=l,student_id=other);session_db.add(ls);await session_db.flush()
    homework=Homework(lesson_student_id=ls.id,title='Other personal assignment',deadline=datetime.now(UTC)+timedelta(days=1))
    session_db.add(homework);await session_db.commit()
    assert (await client_for_tests.delete(f'/courses/{c}/students/me',headers=auth(w['accounts']['s1'][1]))).status_code==204
    # Recipient writes stay personal even when the legacy lesson has several participants.
    r=await client_for_tests.post(f'/homeworks/{homework.id}/submissions',headers=auth(w['accounts']['s2'][1]),data={'text_content':'active recipient'})
    assert r.status_code==201,r.text
    assert (await client_for_tests.get(f'/homeworks/{homework.id}/submissions',headers=auth(w['accounts']['s1'][1]))).status_code==404


@pytest.mark.asyncio
async def test_patch_archive_sets_stable_timestamp_and_requires_admin_restore(client_for_tests, world):
    cid = world['courses'][0].id
    teacher = auth(world['accounts']['t1'][1])
    r = await client_for_tests.patch(f'/courses/{cid}', headers=teacher, json={'is_deleted': True})
    assert r.status_code == 200, r.text
    assert r.json()['is_deleted'] and r.json()['deleted_at']
    stamp = r.json()['deleted_at']
    r = await client_for_tests.delete(f'/courses/{cid}', headers=teacher)
    assert r.status_code == 200 and r.json()['deleted_at'] == stamp
    assert (await client_for_tests.patch(f'/courses/{cid}', headers=teacher,
                                       json={'is_deleted': False})).status_code == 403
    r = await client_for_tests.post(f'/courses/{cid}/restore',
                                   headers=auth(world['accounts']['admin'][1]))
    assert r.status_code == 200 and not r.json()['is_deleted']


@pytest.mark.asyncio
async def test_public_patch_selects_standard_avatar(client_for_tests, world):
    cid = world['courses'][0].id
    r = await client_for_tests.patch(f'/courses/{cid}',
        headers=auth(world['accounts']['t1'][1]), json={'avatar_type': 'mathematics'})
    assert r.status_code == 200, r.text
    assert r.json()['avatar_type'] == 'mathematics'
    assert r.json()['avatar_path'] is None
