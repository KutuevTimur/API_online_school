"""Object boundaries: a shared student never joins two teachers' data scopes."""
from datetime import datetime, UTC

import pytest
import pytest_asyncio
from sqlalchemy import select, delete, update

from src.modules.courses.models import Course
from src.modules.homework_submissions.models import HomeworkSubmissionFile
from src.modules.lesson_students.models import LessonStudent
from src.modules.student_courses.models import StudentCourse
from src.modules.students.models import Student
from src.modules.teacher_students.models import TeacherStudent
from src.modules.teachers.models import Teacher
from src.modules.users.models import User, UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO
from tests.modules.lessons.fixtures.models_dto import CreateLessonFixtureDTO
from tests.modules.lesson_students.fixtures.models_dto import CreateLessonStudentFixtureDTO
from tests.modules.homeworks.fixtures.models_dto import CreateHomeworkFixtureDTO
from tests.modules.lectures.fixtures.models_dto import CreateLectureFixtureDTO
from tests.modules.homework_submissions.fixtures.models_dto import CreateHomeworkSubmissionFixtureDTO


def auth(token):
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def world(create_user_fixture, create_course_fixture, create_lesson_fixture,
                create_lesson_student_fixture, create_homework_fixture, create_lecture_fixture,
                create_homework_submission_fixture, session_db, tmp_path, path_builder_fixture):
    accounts = {}
    for name, role in [('t1', UserRole.TEACHER), ('t2', UserRole.TEACHER),
                       ('s1', UserRole.STUDENT), ('s2', UserRole.STUDENT), ('admin', UserRole.ADMIN)]:
        accounts[name] = await create_user_fixture(CreateUserFixtureDTO(role=role))
    teachers = [await session_db.scalar(select(Teacher).where(Teacher.user_id == accounts[n][0].id)) for n in ['t1','t2']]
    students = [await session_db.scalar(select(Student).where(Student.user_id == accounts[n][0].id)) for n in ['s1','s2']]
    for t in teachers:
        session_db.add(TeacherStudent(teacher_id=t.id, student_id=students[0].id))
    students[0].middle_name = 'PRIVATE MIDDLE NAME'
    avatar = path_builder_fixture.get_avatar_user(accounts['s1'][0].id)
    avatar.parent.mkdir(parents=True, exist_ok=True)
    avatar.write_bytes(b'avatar synthetic')
    students[0].avatar_path = str(avatar)
    await session_db.commit()
    courses=[]; lessons=[]; recipients=[]; homeworks=[]; lectures=[]; submissions=[]; files=[]
    for i, t in enumerate(teachers):
        course=await create_course_fixture(CreateCourseFixtureDTO(teacher_id=t.id))
        courses.append(course)
        session_db.add(StudentCourse(student_id=students[0].id, course_id=course.id))
        await session_db.commit()
        lesson=await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=t.id, course_id=course.id))
        lessons.append(lesson)
        ls=await create_lesson_student_fixture(CreateLessonStudentFixtureDTO(lesson_id=lesson.id,student_id=students[0].id))
        recipients.append(ls)
        h=await create_homework_fixture(CreateHomeworkFixtureDTO(lesson_student_id=ls.id))
        l=await create_lecture_fixture(CreateLectureFixtureDTO(lesson_student_id=ls.id))
        sub=await create_homework_submission_fixture(CreateHomeworkSubmissionFixtureDTO(homework_id=h.id))
        path=path_builder_fixture.config.paths.homework_submissions/f'{i}.pdf'; path.write_bytes(b'%PDF synthetic fixture')
        from src.modules.homeworks.models import Homework
        from src.modules.lectures.models import Lecture
        await session_db.execute(update(Homework).where(Homework.id==h.id).values(pdf_file_path=str(path),pdf_file_name='hw.pdf'))
        await session_db.execute(update(Lecture).where(Lecture.id==l.id).values(pdf_file_path=str(path),pdf_file_name='lecture.pdf'))
        f=HomeworkSubmissionFile(submission_id=sub.id, original_file_path=str(path),original_file_name='answer.pdf',
                                 original_file_type='pdf',pdf_file_path=str(path),pdf_file_name='answer.pdf')
        session_db.add(f); await session_db.commit()
        homeworks.append(h); lectures.append(l); submissions.append(sub); files.append(f)
    return dict(accounts=accounts,teachers=teachers,students=students,courses=courses,lessons=lessons,
                recipients=recipients,homeworks=homeworks,lectures=lectures,submissions=submissions,files=files,avatar=avatar)


def urls(w, i):
    c=w['courses'][i].id; l=w['lessons'][i].id; s=w['accounts']['s1'][0].id
    h=w['homeworks'][i].id; sub=w['submissions'][i].id
    q=f'lesson_id={l}&student_user_id={s}'
    return [f'/courses/{c}',f'/lessons/{l}',f'/courses/{c}/students',
            f'/lectures?{q}',f'/lectures/{w["lectures"][i].id}/file?{q}',
            f'/homeworks?{q}',f'/homeworks/{h}/file?{q}',f'/homeworks/{h}/submissions',
            f'/submissions/{sub}?homework_id={h}',
            f'/submissions/{sub}/files/{w["files"][i].id}?homework_id={h}']


@pytest.mark.asyncio
@pytest.mark.parametrize('actor,index,expected', [('t1',0,200),('t1',1,404),('t2',0,404),('t2',1,200),
                                                ('s2',0,404),('s1',0,200),('s1',1,200),('admin',0,200),('admin',1,200)])
async def test_read_matrix(client_for_tests,world,actor,index,expected):
    for url in urls(world,index):
        # Student roster is a teacher/admin operation.
        status=(403 if actor == 's1' else 404) if actor.startswith('s') and url.endswith('/students') else expected
        r=await client_for_tests.get(url,headers=auth(world['accounts'][actor][1]))
        assert r.status_code==status,(url,r.status_code,r.text)
        if r.status_code==200 and 'application/json' in r.headers.get('content-type',''):
            assert 'PRIVATE MIDDLE NAME' not in r.text
            assert str(world['avatar'].parent) not in r.text


@pytest.mark.asyncio
@pytest.mark.parametrize('actor', ['t1','t2','s1','s2','admin'])
async def test_scoped_counts_filters_and_offset(client_for_tests,world,actor):
    headers=auth(world['accounts'][actor][1]); w=world
    expected={'t1':[0],'t2':[1],'s1':[0,1],'s2':[],'admin':[0,1]}[actor]
    for endpoint,key in [('/courses','courses'),('/lessons','lessons')]:
        r=await client_for_tests.get(endpoint,headers=headers,params={'limit':1,'offset':99})
        assert r.status_code==200 and r.json()['items']==[]
        assert r.json()['total']==len(expected)
        r=await client_for_tests.get(endpoint,headers=headers)
        assert {o['id'] for o in r.json()['items']}=={w[key][i].id for i in expected}
    r=await client_for_tests.get('/courses',headers=headers,params={'teacher_user_id':w['accounts']['t2'][0].id})
    assert {o['id'] for o in r.json()['items']}==({w['courses'][1].id} if 1 in expected else set())


@pytest.mark.asyncio
async def test_profile_d01_and_avatar(client_for_tests,world,session_db):
    w=world;s=w['accounts']['s1'][0];t=w['accounts']['t1'][0]
    for name in ['t1','t2']:
        headers=auth(w['accounts'][name][1])
        r=await client_for_tests.get(f'/users/{s.id}',headers=headers)
        assert r.status_code==200
        assert set(r.json())=={'user_id','username','first_name','last_name','avatar_path','school_grade'}
        assert r.json()['avatar_path']==f'/users/{s.id}/avatar'
        r=await client_for_tests.get('/users/students?limit=1&offset=99',headers=headers)
        assert r.json()['total']==1 and r.json()['items']==[]
        r=await client_for_tests.get('/users/students',headers=headers)
        assert r.json()['items'][0]['username']==s.username
        assert 'email' not in r.text and 'middle_name' not in r.text
        assert (await client_for_tests.get(f'/users/{s.id}/avatar',headers=headers)).status_code==200
        assert (await client_for_tests.patch(f'/users/{s.id}',headers=headers,json={'first_name':'forbidden'})).status_code==403
        assert (await client_for_tests.delete(f'/users/{s.id}/avatar',headers=headers)).status_code==403
    for name in ['s2']:
        for suffix in ['', '/avatar']:
            assert (await client_for_tests.get(f'/users/{s.id}{suffix}',headers=auth(w['accounts'][name][1]))).status_code==404
    assert (await client_for_tests.get(f'/users/{t.id}',headers=auth(w['accounts']['t2'][1]))).status_code==404
    headers=auth(w['accounts']['s1'][1])
    assert (await client_for_tests.get('/users/teachers',headers=headers)).json()['total']==2
    for field,value in [('is_active',False),('role','admin')]:
        assert (await client_for_tests.patch(f'/users/{s.id}',headers=headers,json={field:value})).status_code==422
    assert (await client_for_tests.patch(f'/users/{s.id}/account-status',headers=headers,json={'is_active':False})).status_code==403
    await session_db.execute(update(TeacherStudent).where(TeacherStudent.teacher_id==w['teachers'][0].id).values(ended_at=datetime.now(UTC)))
    await session_db.commit()
    assert (await client_for_tests.get(f'/users/{s.id}',headers=auth(w['accounts']['t1'][1]))).status_code==404
    assert (await client_for_tests.get(f'/users/{s.id}',headers=auth(w['accounts']['t2'][1]))).status_code==200


@pytest.mark.asyncio
async def test_foreign_writes_and_parent_id_substitution(client_for_tests,world,session_db):
    w=world; headers=auth(w['accounts']['t1'][1]);c=w['courses'][1].id;l=w['lessons'][1].id;s=w['accounts']['s1'][0].id
    for method,url,kwargs in [
        ('patch',f'/courses/{c}',{'json':{'name':'bad'}}),('delete',f'/courses/{c}',{}),
        ('patch',f'/lessons/{l}',{'json':{'title':'bad'}}),('delete',f'/lessons/{l}',{}),
        ('post',f'/courses/{c}/students',{'json':{'student_user_id':s}}),
        ('delete',f'/courses/{c}/students/{s}',{}),
        ('post',f'/lessons/{l}/students',{'json':{'student_user_id':s}}),
        ('delete',f'/lessons/{l}/students/{s}',{}),
        ('delete',f'/homeworks/{w["homeworks"][1].id}?lesson_id={l}&student_user_id={s}',{}),
        ('delete',f'/lectures/{w["lectures"][1].id}?lesson_id={l}&student_user_id={s}',{}),
        ('patch',f'/submissions/{w["submissions"][1].id}/teacher?homework_id={w["homeworks"][1].id}',{'json':{'grade':5,'expected_version':1}}),
    ]:
        r=await getattr(client_for_tests,method)(url,headers=headers,**kwargs)
        assert r.status_code==404,(url,r.status_code,r.text)
    # A valid parent cannot authorize another parent's file/submission.
    h=w['homeworks'][0].id;sub=w['submissions'][0].id
    for url in [f'/submissions/{w["submissions"][1].id}?homework_id={h}',
                f'/submissions/{sub}/files/{w["files"][1].id}?homework_id={h}',
                f'/lectures/{w["lectures"][1].id}/file?lesson_id={w["lessons"][0].id}&student_user_id={s}',
                f'/homeworks/{w["homeworks"][1].id}/file?lesson_id={w["lessons"][0].id}&student_user_id={s}']:
        assert (await client_for_tests.get(url,headers=headers)).status_code==404
    assert (await client_for_tests.delete(f'/courses/{w["courses"][0].id}?hard=true',headers=headers)).status_code==403
    assert await session_db.get(Course,w['courses'][0].id) is not None


@pytest.mark.asyncio
async def test_no_profile_does_not_remove_list_scope(client_for_tests,world,session_db):
    user,token=world['accounts']['s2']
    await session_db.execute(delete(Student).where(Student.user_id==user.id));await session_db.commit()
    for endpoint in ['/courses','/lessons','/homeworks/my','/lectures/my']:
        r=await client_for_tests.get(endpoint,headers=auth(token))
        if endpoint.endswith('/my'):
            assert r.status_code==403
        else:
            assert r.status_code==200 and r.json()['total']==0
    assert (await client_for_tests.get(f'/lessons/{world["lessons"][0].id}',headers=auth(token))).status_code==404


@pytest.mark.asyncio
async def test_teacher_cannot_assign_unlinked_student(client_for_tests,world):
    w=world;headers=auth(w['accounts']['t1'][1]);s=w['accounts']['s2'][0].id
    for url in [f'/courses/{w["courses"][0].id}/students',f'/lessons/{w["lessons"][0].id}/students']:
        assert (await client_for_tests.post(url,headers=headers,json={'student_user_id':s})).status_code==404


@pytest.mark.asyncio
async def test_missing_teacher_profile_and_unknown_ids(client_for_tests,create_user_fixture,world,session_db):
    user,token=await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    await session_db.execute(delete(Teacher).where(Teacher.user_id==user.id));await session_db.commit()
    for endpoint in ['/courses','/lessons','/users/students']:
        r=await client_for_tests.get(endpoint,headers=auth(token))
        assert r.status_code==200 and r.json()['total']==0
    assert (await client_for_tests.post('/courses',headers=auth(token),json={'name':'x','slug':'x'})).status_code==403
    for url in ['/courses/2147483647','/lessons/2147483647','/users/2147483647']:
        assert (await client_for_tests.get(url,headers=auth(token))).status_code==404


@pytest.mark.asyncio
async def test_personal_recipient_same_lesson_and_avatar_alias(client_for_tests,world,session_db,path_builder_fixture):
    w=world;s2=w['students'][1];l=w['lessons'][0].id;h=w['homeworks'][0].id
    session_db.add(LessonStudent(lesson_id=l,student_id=s2.id));await session_db.commit()
    headers=auth(w['accounts']['s2'][1])
    # A dangling personal recipient is insufficient without course membership (T07).
    assert (await client_for_tests.get(f'/lessons/{l}',headers=headers)).status_code==404
    session_db.add(StudentCourse(course_id=w['courses'][0].id,student_id=s2.id));await session_db.commit()
    assert (await client_for_tests.get(f'/lessons/{l}',headers=headers)).status_code==200
    assert (await client_for_tests.get(f'/homeworks?lesson_id={l}&student_user_id={w["accounts"]["s1"][0].id}',headers=headers)).status_code==404
    assert (await client_for_tests.get(f'/homeworks/{h}/submissions',headers=headers)).status_code==404
    path=path_builder_fixture.get_avatar_course(w['courses'][0].id)
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'course avatar')
    await session_db.execute(update(Course).where(Course.id==w['courses'][0].id).values(avatar_path=str(path)))
    await session_db.commit()
    for actor,status in [('t1',200),('t2',404),('s1',200),('s2',200),('admin',200)]:
        assert (await client_for_tests.get(f'/courses/{w["courses"][0].id}/avatar',headers=auth(w['accounts'][actor][1]))).status_code==status
    for endpoint in [f'/courses/{w["courses"][0].id}/avatar',f'/course_avatare/{w["courses"][0].id}']:
        assert (await client_for_tests.patch(endpoint,headers=auth(w['accounts']['t2'][1]),files={'avatar':('x.png',b'invalid','image/png')})).status_code==404
    assert path.read_bytes()==b'course avatar'
    r=await client_for_tests.get(f'/courses/{w["courses"][0].id}',headers=auth(w['accounts']['t1'][1]))
    assert r.json()['avatar_path']==f'/courses/{w["courses"][0].id}/avatar'


@pytest.mark.asyncio
async def test_submission_write_roles_and_upload_boundaries(client_for_tests,world):
    w=world;h=w['homeworks'][0].id;sub=w['submissions'][0].id
    for actor in ['t1','admin']:
        headers=auth(w['accounts'][actor][1])
        for url in [f'/homeworks/{h}/submissions',f'/submissions/{sub}/student?homework_id={h}']:
            method=client_for_tests.post if '/homeworks/' in url else client_for_tests.patch
            assert (await method(url,headers=headers,data={'text_content':'forbidden'})).status_code==403
    for actor,status in [('t2',404),('s2',404)]:
        headers=auth(w['accounts'][actor][1])
        assert (await client_for_tests.post(f'/homeworks/{h}/submissions',headers=headers,data={'text_content':'bad'})).status_code==status
        assert (await client_for_tests.delete(f'/submissions/{sub}?homework_id={h}',headers=headers)).status_code==status
    headers=auth(w['accounts']['t2'][1])
    form={'lesson_id':str(w['lessons'][0].id),'student_user_id':str(w['accounts']['s1'][0].id)}
    assert (await client_for_tests.post('/lectures',headers=headers,data=form,files={'file':('bad.pdf',b'bad','application/pdf')})).status_code==404
    assert (await client_for_tests.post('/homeworks',headers=headers,data={**form,'title':'bad'})).status_code==404


@pytest.mark.asyncio
async def test_link_and_enrollment_required_independently(client_for_tests,world,session_db):
    w=world;l=w['lessons'][0].id;s=w['accounts']['s2'][0].id
    headers=auth(w['accounts']['t1'][1]);c=w['courses'][0].id
    session_db.add(TeacherStudent(teacher_id=w['teachers'][0].id,student_id=w['students'][1].id));await session_db.commit()
    r=await client_for_tests.post(f'/lessons/{l}/students',headers=headers,json={'student_user_id':s})
    assert r.status_code==403
    r=await client_for_tests.post(f'/courses/{c}/students',headers=headers,json={'student_user_id':s})
    assert r.status_code==201
    assert r.json()['student_user_id']==s and 'student_id' not in r.json()
    r=await client_for_tests.post(f'/lessons/{l}/students',headers=headers,json={'student_user_id':s})
    assert r.status_code==201


@pytest.mark.asyncio
async def test_admin_status_audit_and_immediate_revocation(client_for_tests,world,session_db):
    from src.modules.account_invitations.models import AccountAudit
    w=world;user,token=w['accounts']['s1'];headers=auth(w['accounts']['admin'][1])
    r=await client_for_tests.patch(f'/users/{user.id}',headers=headers,json={'first_name':'Admin edit'})
    assert r.status_code==200
    r=await client_for_tests.patch(f'/users/{user.id}/account-status',headers=headers,json={'is_active':False})
    assert r.status_code==200
    for url in ['/users/me','/courses',f'/users/{user.id}/avatar']:
        assert (await client_for_tests.get(url,headers=auth(token))).status_code==401
    actions=set((await session_db.scalars(select(AccountAudit.action).where(AccountAudit.target_user_id==user.id))).all())
    assert {'profile_update','account_status'} <= actions
    # The other student remains active.
    assert (await client_for_tests.get('/users/me',headers=auth(w['accounts']['s2'][1]))).status_code==200
