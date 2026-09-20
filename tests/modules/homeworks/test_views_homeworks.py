from datetime import datetime, timezone
import pytest
from typing import List
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.lessons.fixtures.models_dto import CreateLessonFixtureDTO
from tests.modules.lesson_students.fixtures.models_dto import CreateLessonStudentFixtureDTO
from tests.modules.homeworks.fixtures.models_dto import CreateHomeworkFixtureDTO
from sqlalchemy import select
from src.modules.teachers.models import Teacher
from src.modules.students.models import Student
from src.modules.homeworks.models_dto import HomeworkResponseDTO, CreateHomeworkFormRequestDTO
from pydantic import TypeAdapter


@pytest.mark.asyncio
async def test_create_homework(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_lesson_student_fixture,
    create_homework_fixture,
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

    await create_lesson_student_fixture(CreateLessonStudentFixtureDTO(lesson_id=lesson.id, student_id=student_table_id))

    hw_dto = CreateHomeworkFormRequestDTO(
        lesson_id=lesson.id,
        student_user_id=student.id,
        title="Math Homework",
        deadline=datetime(2030, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
        description="Calculate 2+2"
    )

    files = {
        "file": ("test_hw.pdf", b"dummy pdf content", "application/pdf")
    }
    
    res_hw = await client_for_tests.post(
        "/homeworks",
        data=hw_dto.model_dump(mode="json", exclude_none=True),
        files=files,
        headers={"Authorization": f"Bearer {t_token}"},
    )
    
    assert res_hw.status_code == 201
    res_dto = HomeworkResponseDTO.model_validate(res_hw.json())
    assert res_dto.title == "Math Homework"
    assert res_dto.pdf_file_name is not None


@pytest.mark.asyncio
async def test_get_homeworks_list(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_lesson_student_fixture,
    create_homework_fixture,
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

    ls = await create_lesson_student_fixture(CreateLessonStudentFixtureDTO(lesson_id=lesson.id, student_id=student_table_id))
    homework = await create_homework_fixture(CreateHomeworkFixtureDTO(lesson_student_id=ls.id))

    res_list = await client_for_tests.get(
        f"/homeworks?lesson_id={lesson.id}&student_user_id={student.id}",
        headers={"Authorization": f"Bearer {t_token}"},
    )
    
    assert res_list.status_code == 200
    res_dto_list = TypeAdapter(List[HomeworkResponseDTO]).validate_python(res_list.json())
    assert len(res_dto_list) == 1


@pytest.mark.asyncio
async def test_download_homework_file(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_lesson_student_fixture,
    create_homework_fixture,
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

    await create_lesson_student_fixture(CreateLessonStudentFixtureDTO(lesson_id=lesson.id, student_id=student_table_id))

    hw_dto = CreateHomeworkFormRequestDTO(
        lesson_id=lesson.id,
        student_user_id=student.id,
        title="Title",
        deadline=datetime(2030, 12, 31, 23, 59, 59, tzinfo=timezone.utc),
    )
    upload_res = await client_for_tests.post(
        "/homeworks",
        data=hw_dto.model_dump(mode="json", exclude_none=True),
        files={"file": ("test_hw.pdf", b"dummy pdf content", "application/pdf")},
        headers={"Authorization": f"Bearer {t_token}"},
    )
    res_dto = HomeworkResponseDTO.model_validate(upload_res.json())
    homework_id = res_dto.id

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
    create_lesson_student_fixture,
    create_homework_fixture,
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

    ls = await create_lesson_student_fixture(CreateLessonStudentFixtureDTO(lesson_id=lesson.id, student_id=student_table_id))
    homework = await create_homework_fixture(CreateHomeworkFixtureDTO(lesson_student_id=ls.id))

    res_del = await client_for_tests.delete(
        f"/homeworks/{homework.id}?lesson_id={lesson.id}&student_user_id={student.id}",
        headers={"Authorization": f"Bearer {t_token}"},
    )
    
    assert res_del.status_code == 200

    res_list_after = await client_for_tests.get(
        f"/homeworks?lesson_id={lesson.id}&student_user_id={student.id}",
        headers={"Authorization": f"Bearer {t_token}"},
    )
    res_dto_list = TypeAdapter(List[HomeworkResponseDTO]).validate_python(res_list_after.json())
    assert len(res_dto_list) == 0
