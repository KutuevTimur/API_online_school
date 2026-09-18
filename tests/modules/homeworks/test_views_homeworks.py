import pytest
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.lessons.fixtures.models_dto import CreateLessonFixtureDTO
from sqlalchemy import select
from src.modules.teachers.models import Teacher
from src.modules.students.models import Student
from src.modules.homeworks.models import Homework
from src.modules.lesson_students.models import LessonStudent
from datetime import datetime, timezone


@pytest.mark.asyncio
async def test_create_homework(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    not_open_session_db,
    session_db,
):
    teacher, t_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, s_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id
        s_db = await session.scalar(select(Student).where(Student.user_id == student.id))
        student_table_id = s_db.id

    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id))

    session_db.add(LessonStudent(lesson_id=lesson.id, student_id=student_table_id))
    await session_db.commit()

    hw_data = {
        "lesson_id": lesson.id,
        "student_user_id": student.id,
        "title": "Math Homework",
        "deadline": "2030-12-31T23:59:59Z",
        "description": "Calculate 2+2"
    }

    files = {
        "file": ("test_hw.pdf", b"dummy pdf content", "application/pdf")
    }
    
    res_hw = await client_for_tests.post(
        "/homeworks",
        data=hw_data,
        files=files,
        headers={"Authorization": f"Bearer {t_token}"},
    )
    
    assert res_hw.status_code == 201
    hw = res_hw.json()
    assert hw["title"] == "Math Homework"
    assert hw["pdf_file_name"] is not None


@pytest.mark.asyncio
async def test_get_homeworks_list(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    not_open_session_db,
    session_db,
):
    teacher, t_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id
        s_db = await session.scalar(select(Student).where(Student.user_id == student.id))
        student_table_id = s_db.id

    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id))

    ls = LessonStudent(lesson_id=lesson.id, student_id=student_table_id)
    session_db.add(ls)
    await session_db.commit()
    await session_db.refresh(ls)

    homework = Homework(
        lesson_student_id=ls.id,
        title="Test list",
        deadline=datetime.now(timezone.utc),
    )
    session_db.add(homework)
    await session_db.commit()

    res_list = await client_for_tests.get(
        f"/homeworks?lesson_id={lesson.id}&student_user_id={student.id}",
        headers={"Authorization": f"Bearer {t_token}"},
    )
    
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1


@pytest.mark.asyncio
async def test_download_homework_file(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    not_open_session_db,
    session_db,
):
    teacher, t_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id
        s_db = await session.scalar(select(Student).where(Student.user_id == student.id))
        student_table_id = s_db.id

    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id))

    session_db.add(LessonStudent(lesson_id=lesson.id, student_id=student_table_id))
    await session_db.commit()

    upload_res = await client_for_tests.post(
        "/homeworks",
        data={
            "lesson_id": lesson.id,
            "student_user_id": student.id,
            "title": "Title",
            "deadline": "2030-12-31T23:59:59Z",
        },
        files={"file": ("test_hw.pdf", b"dummy pdf content", "application/pdf")},
        headers={"Authorization": f"Bearer {t_token}"},
    )
    homework_id = upload_res.json()["id"]

    res_download = await client_for_tests.get(
        f"/homeworks/{homework_id}/file?lesson_id={lesson.id}&student_user_id={student.id}",
        headers={"Authorization": f"Bearer {t_token}"},
    )
    
    assert res_download.status_code == 200
    assert res_download.content == b"dummy pdf content"


@pytest.mark.asyncio
async def test_delete_homework(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    not_open_session_db,
    session_db,
):
    teacher, t_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id
        s_db = await session.scalar(select(Student).where(Student.user_id == student.id))
        student_table_id = s_db.id

    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id))

    ls = LessonStudent(lesson_id=lesson.id, student_id=student_table_id)
    session_db.add(ls)
    await session_db.commit()
    await session_db.refresh(ls)

    homework = Homework(
        lesson_student_id=ls.id,
        title="To be deleted",
        deadline=datetime.now(timezone.utc),
    )
    session_db.add(homework)
    await session_db.commit()

    res_del = await client_for_tests.delete(
        f"/homeworks/{homework.id}?lesson_id={lesson.id}&student_user_id={student.id}",
        headers={"Authorization": f"Bearer {t_token}"},
    )
    
    assert res_del.status_code == 200

    res_list_after = await client_for_tests.get(
        f"/homeworks?lesson_id={lesson.id}&student_user_id={student.id}",
        headers={"Authorization": f"Bearer {t_token}"},
    )
    assert len(res_list_after.json()) == 0
