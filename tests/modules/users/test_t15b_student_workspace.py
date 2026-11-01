"""Shared school grade and idempotent personal workspace boundaries."""
import asyncio
from datetime import datetime, UTC
import pytest
import pytest_asyncio
from sqlalchemy import select, func
from src.modules.users.models import UserRole
from src.modules.students.models import Student
from src.modules.teachers.models import Teacher
from src.modules.teacher_students.models import TeacherStudent
from src.modules.courses.models import Course
from src.modules.student_courses.models import StudentCourse
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO

@pytest_asyncio.fixture
async def actors(create_user_fixture, session_db):
    accounts = {key: await create_user_fixture(CreateUserFixtureDTO(role=role)) for key, role in [
        ('t1', UserRole.TEACHER), ('t2', UserRole.TEACHER), ('foreign', UserRole.TEACHER),
        ('student', UserRole.STUDENT), ('other', UserRole.STUDENT), ('admin', UserRole.ADMIN)]}
    student = await session_db.scalar(select(Student).where(Student.user_id == accounts['student'][0].id))
    for key in ['t1', 't2']:
        teacher = await session_db.scalar(select(Teacher).where(Teacher.user_id == accounts[key][0].id))
        session_db.add(TeacherStudent(teacher_id=teacher.id, student_id=student.id))
    await session_db.commit()
    return accounts

def auth(actors, key):
    return {'Authorization': 'Bearer ' + actors[key][1]}

@pytest.mark.asyncio
async def test_shared_grade_scoped_conflict_and_filter(client_for_tests, actors):
    c=client_for_tests; sid=actors['student'][0].id; url=f'/users/{sid}/school-grade'
    r=await c.patch(url, headers=auth(actors,'t1'), json={'school_grade':10,'expected_school_grade':None})
    assert r.status_code==200, r.text
    assert r.json()['school_grade']==10
    assert (await c.get(f'/users/{sid}',headers=auth(actors,'t2'))).json()['school_grade']==10
    assert (await c.get(f'/users/{sid}',headers=auth(actors,'student'))).json()['student']['school_grade']==10
    r=await c.patch(url, headers=auth(actors,'t2'),json={'school_grade':11,'expected_school_grade':None})
    assert r.status_code==409
    assert (await c.patch(url,headers=auth(actors,'foreign'),json={'school_grade':11,'expected_school_grade':10})).status_code in (403,404)
    assert (await c.patch(f'/users/{sid}',headers=auth(actors,'t1'),json={'first_name':'Unauthorized'})).status_code==403
    assert (await c.patch(url,headers=auth(actors,'t1'),json={'school_grade':11,'expected_school_grade':10,'first_name':'Unauthorized'})).status_code==422
    for grade, total in [(10,1),(11,0)]:
        r=await c.get('/users/students',params={'school_grade':grade,'limit':20},headers=auth(actors,'t2'))
        assert r.status_code==200 and r.json()['total']==total
    r=await c.patch(url,headers=auth(actors,'t2'),json={'school_grade':11,'expected_school_grade':10})
    assert r.status_code==200 and r.json()['school_grade']==11

@pytest.mark.parametrize('grade', [0,12,-1,1.5,True,False])
@pytest.mark.asyncio
async def test_grade_validation(client_for_tests, actors, grade):
    r=await client_for_tests.patch(f"/users/{actors['student'][0].id}/school-grade",headers=auth(actors,'t1'),json={'school_grade':grade,'expected_school_grade':None})
    assert r.status_code==422

@pytest.mark.asyncio
async def test_workspace_concurrent_retry_own_teacher_and_archive(client_for_tests, actors, session_db, not_open_session_db, app_fastapi, config_fix):
    c=client_for_tests; sid=actors['student'][0].id; url=f'/courses/personal/{sid}'
    assert (await c.get(url,headers=auth(actors,'t1'))).json() is None
    assert (await c.post(url,headers=auth(actors,'foreign'))).status_code in (403,404)
    assert (await c.post(url,headers=auth(actors,'student'))).status_code==403
    from src.modules.courses.depends import get_courses_service
    async def start():
        async with not_open_session_db() as db:
            return await get_courses_service(db, config_fix).personal_workspace(actors['t1'][0], sid, create=True)
    results=await asyncio.gather(*(start() for _ in range(3)))
    ids={r.id for r in results}; assert len(ids)==1
    first=results[0].model_dump(); assert first['teacher_user_id']==actors['t1'][0].id
    assert (await c.get(f"/courses/{first['id']}/students",headers=auth(actors,'t1'))).json()['items'][0]['student_user_id']==sid
    assert (await c.get(url,headers=auth(actors,'t2'))).json() is None
    second=await c.post(url,headers=auth(actors,'t2')); assert second.status_code==200 and second.json()['id']!=first['id']
    assert (await session_db.scalar(select(func.count()).select_from(Course)))==2
    # Archive retained; explicitly starting later creates only one new active space.
    assert (await c.delete(f"/courses/{first['id']}",headers=auth(actors,'t1'))).status_code==200
    assert (await c.get(url,headers=auth(actors,'t1'))).json() is None
    new=await c.post(url,headers=auth(actors,'t1')); assert new.status_code==200 and new.json()['id']!=first['id']
    assert (await c.get(f"/courses/{first['id']}",headers=auth(actors,'t1'))).json()['is_deleted']
    assert (await c.post(url,headers=auth(actors,'t1'))).json()['id']==new.json()['id']

@pytest.mark.asyncio
async def test_ended_link_cannot_change_grade_or_start_workspace(client_for_tests,actors,session_db):
    teacher=await session_db.scalar(select(Teacher).where(Teacher.user_id==actors['t1'][0].id))
    link=await session_db.scalar(select(TeacherStudent).where(TeacherStudent.teacher_id==teacher.id))
    link.ended_at=datetime.now(UTC); await session_db.commit(); sid=actors['student'][0].id
    for method,url,body in [('PATCH',f'/users/{sid}/school-grade',{'school_grade':10,'expected_school_grade':None}),('POST',f'/courses/personal/{sid}',None)]:
        r=await client_for_tests.request(method,url,headers=auth(actors,'t1'),json=body)
        assert r.status_code in (403,404)

@pytest.mark.asyncio
async def test_workspace_failure_rolls_back_both_records(actors, not_open_session_db, config_fix, monkeypatch):
    from unittest.mock import AsyncMock
    from src.modules.courses.depends import get_courses_service
    from src.modules.student_courses.repository import StudentCoursesRepository
    monkeypatch.setattr(StudentCoursesRepository, 'add_student_to_course', AsyncMock(side_effect=RuntimeError('synthetic failure')))
    async with not_open_session_db() as db:
        with pytest.raises(RuntimeError, match='synthetic failure'):
            await get_courses_service(db,config_fix).personal_workspace(actors['t1'][0], actors['student'][0].id, create=True)
        assert await db.scalar(select(func.count()).select_from(Course))==0
        assert await db.scalar(select(func.count()).select_from(StudentCourse))==0

@pytest.mark.asyncio
async def test_register_initial_grade_and_full_name_search(client_for_tests, actors):
    c=client_for_tests
    r=await c.post('/auth/register',headers=auth(actors,'t1'),json={'role':'student','username':'synthetic_graded','first_name':'Иван','last_name':'Петров','school_grade':10})
    assert r.status_code==200
    sid=r.json()['id']
    for q in ['Иван Петров','Петров Иван']:
        result=await c.get('/users/students',params={'q':q,'school_grade':10},headers=auth(actors,'t1'))
        assert result.status_code==200 and result.json()['total']==1
        assert result.json()['items'][0]['school_grade']==10
    assert (await c.get(f'/users/{sid}',headers=auth(actors,'t2'))).status_code in (403,404)

@pytest.mark.asyncio
async def test_student_sort_before_paging_stable_and_scoped(client_for_tests, actors, session_db, create_user_fixture):
    from datetime import timedelta
    teacher = await session_db.scalar(select(Teacher).where(Teacher.user_id == actors['t1'][0].id))
    existing = await session_db.scalar(select(Student).where(Student.user_id == actors['student'][0].id))
    existing.first_name='Same'; existing.last_name='Name'; existing.school_grade=7
    link = await session_db.scalar(select(TeacherStudent).where(TeacherStudent.teacher_id == teacher.id))
    now=datetime.now(UTC); link.started_at=now-timedelta(days=5)
    ids=[existing.user_id]
    for index, grade in enumerate([11, 7, None]):
        user, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
        profile=await session_db.scalar(select(Student).where(Student.user_id==user.id))
        profile.first_name=['Alpha','same','Zed'][index]; profile.last_name='Name'; profile.school_grade=grade
        session_db.add(TeacherStudent(teacher_id=teacher.id, student_id=profile.id, started_at=now-timedelta(days=3 if index==0 else 1)))
        ids.append(user.id)
    await session_db.commit()
    expected={'recent':list(reversed(ids)), 'name':[ids[1],ids[0],ids[2],ids[3]], 'grade_asc':[ids[0],ids[2],ids[1],ids[3]], 'grade_desc':[ids[1],ids[0],ids[2],ids[3]]}
    for sort, ordered in expected.items():
        collected=[]
        for offset in [0,2]:
            response=await client_for_tests.get('/users/students',params={'sort':sort,'limit':2,'offset':offset},headers=auth(actors,'t1'))
            assert response.status_code==200, response.text
            assert response.json()['total']==4
            collected.extend(item['user_id'] for item in response.json()['items'])
        assert collected==ordered
    response=await client_for_tests.get('/users/students',params={'sort':'grade_desc','school_grade':7,'limit':1,'offset':1},headers=auth(actors,'t1'))
    assert response.json()['total']==2 and response.json()['items'][0]['user_id']==ids[2]
    assert (await client_for_tests.get('/users/students',params={'sort':'invalid'},headers=auth(actors,'t1'))).status_code==422
