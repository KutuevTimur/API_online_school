"""T14c contracts on synthetic guarded PostgreSQL."""
import asyncio
import pytest
from sqlalchemy import func, select, update
from tests.modules.auth.test_t06_permissions import world
from tests.modules.homework_submissions.test_t09_lifecycle import headers
from src.modules.users.models import User
from src.modules.teacher_students.models import TeacherStudent
from src.modules.audit_events.models import AuditEvent
from src.modules.course_lifecycle.models import EnrollmentGap


def pair(w, teacher='t1'):
    return f'/teacher_students/{w["accounts"][teacher][0].id}/{w["accounts"]["s1"][0].id}'


@pytest.mark.asyncio
@pytest.mark.parametrize('actor', ['t1', 's1'])
async def test_admin_forbidden(client_for_tests, world, actor):
    for path in ['/admin/users', f'/admin/users/{world["accounts"]["s1"][0].id}', '/teacher_students']:
        assert (await client_for_tests.get(path, headers=headers(world, actor))).status_code == 403
    assert (await client_for_tests.delete(pair(world), headers=headers(world, actor))).status_code == 403


@pytest.mark.asyncio
async def test_admin_search_status_and_safe_profiles(client_for_tests, world, session_db):
    c,w=client_for_tests,world
    uid=w['accounts']['s2'][0].id
    await session_db.execute(update(User).where(User.id==uid).values(
        username=r'Literal%_\Search',is_active=False,is_activated=False))
    await session_db.commit()
    for q, expected in [('literal%_',1),('%',1),('_',1),('\\',1),('missing-name',0)]:
        r=await c.get('/admin/users',params={'q':q,'role':'student','is_active':False,
            'is_activated':False,'offset':99},headers=headers(w,'admin'))
        assert r.status_code==200,r.text
        assert r.json()['total']==expected and r.json()['items']==[]
    r=await c.get(f'/admin/users/{uid}',headers=headers(w,'admin'))
    assert r.status_code==200,r.text
    d=r.json()
    assert d['user_id']==uid and not d['is_active'] and not d['is_activated']
    assert d['first_name'] is not None
    assert not {'id','hashed_password','auth_version','teacher','student','token'} & d.keys()
    assert (await c.get('/admin/users/2147483647',headers=headers(w,'admin'))).status_code==404
    for query in ['q=','q='+('x'*101),'limit=0','limit=101','offset=-1','role=invalid','offset=2147483648']:
        assert (await c.get('/admin/users?'+query,headers=headers(w,'admin'))).status_code==422
    name=w['students'][0].first_name
    r=await c.get('/users/students',params={'q':name.swapcase()},headers=headers(w,'t1'))
    assert r.status_code==200 and r.json()['total']==1
    r=await c.get('/users/students',params={'q':'Literal%_'},headers=headers(w,'t1'))
    assert r.json()['total']==0


@pytest.mark.asyncio
async def test_end_cutoff_history_files_relink(client_for_tests, world, session_db):
    c,w=client_for_tests,world; admin=headers(w,'admin')
    r=await c.get('/teacher_students',headers=admin,params={'limit':1,'offset':99})
    assert r.status_code==200,r.text
    assert r.json()['total']==2 and not r.json()['items']
    r=await c.get('/teacher_students',headers=admin,params={
        'student_user_id':w['accounts']['s1'][0].id,'active':True})
    assert r.json()['total']==2 and len(r.json()['items'])==2
    assert (await c.get('/teacher_students',headers=admin,params={
        'student_user_id':w['accounts']['s2'][0].id})).json()['total']==0
    for query in ['teacher_user_id=0','student_user_id=-1','limit=101','offset=-1']:
        assert (await c.get('/teacher_students?'+query,headers=admin)).status_code==422
    for _ in range(2):
        assert (await c.delete(pair(w),headers=admin)).status_code==204
        r=await c.get('/teacher_students',headers=admin,params={
            'teacher_user_id':w['accounts']['t1'][0].id,'active':False})
        assert r.status_code==200,r.text
        assert r.json()['total']==1
        item=r.json()['items'][0]
        assert set(item['student'])=={'user_id','username','first_name','last_name','avatar_path','school_grade'}
        if _==0: cutoff=item['ended_at']
        else: assert cutoff==item['ended_at']
    assert await session_db.scalar(select(func.count()).select_from(AuditEvent).where(AuditEvent.action=='teacher_student_end'))==1
    assert (await c.get('/users/students',headers=headers(w,'t1'))).json()['total']==0
    assert (await c.get('/users/students',headers=headers(w,'t2'))).json()['total']==1
    for index,mode in [(0,'read_only'),(1,'active')]:
        r=await c.get(f'/homeworks/{w["homeworks"][index].id}',headers=headers(w))
        assert r.status_code==200,r.text
        assert r.json()['access_mode']==mode
        assert (await c.get(r.json()['file']['download_url'],headers=headers(w))).status_code==200
    r=await c.get(f'/admin/users/{w["accounts"]["s1"][0].id}',headers=admin)
    assert r.json()['is_active']
    r=await c.post('/teacher_students',headers=admin,json={
        'teacher_user_id':w['accounts']['t1'][0].id,'student_user_id':w['accounts']['s1'][0].id})
    assert r.status_code==200,r.text
    assert await session_db.scalar(select(func.count()).select_from(EnrollmentGap))==1
    assert (await c.delete(f'/teacher_students/{w["accounts"]["t1"][0].id}/{w["accounts"]["s2"][0].id}',headers=admin)).status_code==404


@pytest.mark.asyncio
async def test_end_rollback(world, config_fix, monkeypatch):
    from src.modules.teacher_students.service import TeacherStudentService
    from src.modules.teacher_students.models_dto import LinkTeacherStudentRequestDTO
    from src.modules.homework_placements.service import HomeworkPlacementsService
    async def fail(*args,**kwargs):
        raise RuntimeError('synthetic recalc failure')
    monkeypatch.setattr(HomeworkPlacementsService,'recalculate_course',fail)
    async with config_fix.db_connection.session_local() as session:
        with pytest.raises(RuntimeError,match='synthetic'):
            await TeacherStudentService(session).end(LinkTeacherStudentRequestDTO(
                teacher_user_id=world['accounts']['t1'][0].id,
                student_user_id=world['accounts']['s1'][0].id),world['accounts']['admin'][0].id)
        link=await session.scalar(select(TeacherStudent).where(TeacherStudent.teacher_id==world['teachers'][0].id))
        assert link.ended_at is None
        assert await session.scalar(select(func.count()).select_from(AuditEvent))==0


@pytest.mark.asyncio
async def test_concurrent_end_relink(world, config_fix):
    from src.modules.teacher_students.service import TeacherStudentService
    from src.modules.teacher_students.models_dto import LinkTeacherStudentRequestDTO
    data=LinkTeacherStudentRequestDTO(teacher_user_id=world['accounts']['t1'][0].id,
        student_user_id=world['accounts']['s1'][0].id)
    async def run(action):
        async with config_fix.db_connection.session_local() as session:
            await getattr(TeacherStudentService(session), action)(data,world['accounts']['admin'][0].id)
    await asyncio.wait_for(asyncio.gather(run('end'),run('end')),10)
    await asyncio.wait_for(asyncio.gather(run('link'),run('end')),10)


@pytest.mark.asyncio
@pytest.mark.parametrize('operation', ['submit', 'move'])
@pytest.mark.parametrize('end_first', [True, False])
async def test_end_serializes_with_writes(world, config_fix, operation, end_first, monkeypatch):
    from datetime import timedelta
    from src.modules.teacher_students.repository import TeacherStudentRepository
    from src.modules.teacher_students.service import TeacherStudentService
    from src.modules.teacher_students.models_dto import LinkTeacherStudentRequestDTO
    from src.modules.homework_submissions.depends import get_homework_submissions_service
    from src.modules.lessons.depends import get_lessons_service
    from src.modules.lessons.models_dto import UpdateLessonRequestDTO
    from src.modules.check_permission.exception import PermissionErrorService
    from src.modules.check_permission.repository import PermissionRepository
    from src.modules.homework_submissions.models import HomeworkSubmission
    from src.modules.lessons.models import Lesson
    w=world
    data=LinkTeacherStudentRequestDTO(teacher_user_id=w['accounts']['t1'][0].id,
        student_user_id=w['accounts']['s1'][0].id)
    async with config_fix.db_connection.session_local() as first, config_fix.db_connection.session_local() as second:
        locked=asyncio.Event(); release=asyncio.Event()
        # Hold the common course lock in the winning transaction so the other must wait.
        if end_first:
            original=TeacherStudentRepository.lock_courses
            async def hold(repo,*args):
                result=await original(repo,*args)
                if repo.session is first:
                    locked.set(); await release.wait()
                return result
            monkeypatch.setattr(TeacherStudentRepository,'lock_courses',hold)
        else:
            method='writable_recipient' if operation=='submit' else 'writable_lesson'
            original=getattr(PermissionRepository,method)
            async def hold(service,*args,**kwargs):
                result=await original(service,*args,**kwargs)
                if service.session is first:
                    locked.set(); await release.wait()
                return result
            monkeypatch.setattr(PermissionRepository,method,hold)
        async def end(session):
            await TeacherStudentService(session).end(data,w['accounts']['admin'][0].id)
        async def write(session):
            if operation=='submit':
                return await get_homework_submissions_service(session=session,config=config_fix).submit_submission(
                    w['accounts']['s1'][0].id,w['homeworks'][0].id,w['submissions'][0].id)
            return await get_lessons_service(session=session).update_lesson(w['accounts']['t1'][0].id,
                w['lessons'][0].id,UpdateLessonRequestDTO(scheduled_at=w['lessons'][0].scheduled_at+timedelta(hours=1)))
        a=asyncio.create_task(end(first) if end_first else write(first))
        await asyncio.wait_for(locked.wait(),5)
        b=asyncio.create_task(write(second) if end_first else end(second))
        await asyncio.sleep(0.05)
        assert not b.done()
        release.set()
        results=await asyncio.wait_for(asyncio.gather(a,b,return_exceptions=True),10)
        assert results[0] is None or not isinstance(results[0],Exception),results
        if end_first:
            assert isinstance(results[1],PermissionErrorService),results
        else:
            assert not isinstance(results[1],Exception),results
        async with config_fix.db_connection.session_local() as check:
            link=await check.scalar(select(TeacherStudent).where(TeacherStudent.teacher_id==w['teachers'][0].id))
            assert link.ended_at is not None
            sub=await check.get(HomeworkSubmission,w['submissions'][0].id)
            if operation=='submit':
                assert sub.status==('draft' if end_first else 'submitted')
            else:
                lesson=await check.get(Lesson,w['lessons'][0].id)
                assert lesson.scheduled_at==w['lessons'][0].scheduled_at+(timedelta(0) if end_first else timedelta(hours=1))


@pytest.mark.asyncio
async def test_relink_keeps_hidden_period(client_for_tests, world, session_db):
    from src.modules.homeworks.models import Homework
    from src.modules.homework_submissions.models import HomeworkSubmission
    c,w=client_for_tests,world; admin=headers(w,'admin')
    assert (await c.delete(pair(w),headers=admin)).status_code==204
    # Synthetic material issued while the teacher link is ended.
    now=await session_db.scalar(select(func.clock_timestamp()))
    await session_db.execute(update(Homework).where(Homework.id==w['homeworks'][0].id).values(created_at=now))
    await session_db.execute(update(HomeworkSubmission).where(HomeworkSubmission.id==w['submissions'][0].id).values(created_at=now))
    await session_db.commit()
    assert (await c.get(f'/homeworks/{w["homeworks"][0].id}',headers=headers(w))).status_code==404
    assert (await c.post('/teacher_students',headers=admin,json={
        'teacher_user_id':w['accounts']['t1'][0].id,'student_user_id':w['accounts']['s1'][0].id})).status_code==200
    assert (await c.get(f'/homeworks/{w["homeworks"][0].id}',headers=headers(w))).status_code==404
    assert (await c.get(f'/lectures/{w["lectures"][0].id}',headers=headers(w))).status_code==200
    assert (await c.get(f'/homeworks/{w["homeworks"][1].id}',headers=headers(w))).status_code==200


@pytest.mark.asyncio
async def test_end_rollback_after_audit(world, config_fix, monkeypatch):
    from src.modules.teacher_students.service import TeacherStudentService
    from src.modules.teacher_students.models_dto import LinkTeacherStudentRequestDTO
    from src.modules.audit_events.service import AuditEventsService
    from src.modules.homework_placements.service import HomeworkPlacementsService
    from src.modules.homework_placements.models import HomeworkDeadlineEvent, HomeworkPlacement
    from src.modules.homeworks.models import Homework
    original=AuditEventsService.stage
    def fail(*args,**kwargs):
        original(*args,**kwargs)
        raise RuntimeError('synthetic audit failure')
    monkeypatch.setattr(AuditEventsService,'stage',fail)
    async with config_fix.db_connection.session_local() as session:
        baseline_events=await session.scalar(select(func.count()).select_from(HomeworkDeadlineEvent))
        baseline_deadline=(await session.get(Homework,world['homeworks'][0].id)).deadline
        # A real deadline/event staged during recalc must roll back with the end.
        async def stage_recalc(service, course_id, reason):
            homework=await session.get(Homework,world['homeworks'][0].id)
            placement=await session.scalar(select(HomeworkPlacement).where(HomeworkPlacement.homework_id==homework.id))
            placement.due_at=await session.scalar(select(func.clock_timestamp()))
            homework.deadline=placement.due_at
            service.record(placement,reason)
            await session.flush()
        monkeypatch.setattr(HomeworkPlacementsService,'recalculate_course',stage_recalc)
        with pytest.raises(RuntimeError,match='synthetic audit'):
            await TeacherStudentService(session).end(LinkTeacherStudentRequestDTO(
                teacher_user_id=world['accounts']['t1'][0].id,
                student_user_id=world['accounts']['s1'][0].id),world['accounts']['admin'][0].id)
        assert (await session.scalar(select(TeacherStudent).where(TeacherStudent.teacher_id==world['teachers'][0].id))).ended_at is None
        assert await session.scalar(select(func.count()).select_from(AuditEvent))==0
        assert await session.scalar(select(func.count()).select_from(HomeworkPlacement))==2
        assert await session.scalar(select(func.count()).select_from(HomeworkDeadlineEvent))==baseline_events
        assert (await session.get(Homework,world['homeworks'][0].id)).deadline==baseline_deadline


@pytest.mark.asyncio
async def test_openapi_response_leak_scan(app_fastapi):
    schema=app_fastapi.openapi()
    assert '/admin/users' in schema['paths'] and '/users/admin/users' not in schema['paths']
    forbidden={'hashed_password','auth_version','refresh_digest','token_hash','invite_token',
               'teacher_id','student_id','original_file_path','pdf_file_path'}
    def inspect(node):
        if isinstance(node,dict):
            if '$ref' in node:
                inspect(schema['components']['schemas'][node['$ref'].split('/')[-1]])
            assert not forbidden.intersection(node.get('properties',{}))
            for key,value in node.items():
                if key!='$ref': inspect(value)
        elif isinstance(node,list):
            for value in node: inspect(value)
    for path in ['/admin/users','/admin/users/{user_id}','/teacher_students','/users/students']:
        inspect(schema['paths'][path]['get']['responses']['200'])
