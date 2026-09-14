import pytest
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.lessons.fixtures.models_dto import CreateLessonFixtureDTO
from sqlalchemy import select
from src.modules.teachers.models import Teacher
from src.modules.lesson_students.models import LessonStudent


@pytest.mark.asyncio
async def test_add_and_remove_student(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    not_open_session_db,
    session_db,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, student_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id

    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id))

    payload = {"student_user_id": student.id}
    response = await client_for_tests.post(
        f"/lessons/{lesson.id}/students",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    session_db.expire_all()

    get_res = await client_for_tests.get(
        f"/lessons/{lesson.id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert get_res.status_code == 200

    del_res = await client_for_tests.delete(
        f"/lessons/{lesson.id}/students/{student.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 200

    async with not_open_session_db() as local_session:
        from src.modules.students.models import Student
        s_db = await local_session.scalar(select(Student).where(Student.user_id == student.id))
        ls_db = await local_session.scalar(select(LessonStudent).where(
            LessonStudent.lesson_id == lesson.id,
            LessonStudent.student_id == s_db.id,
        ))
        assert ls_db is None
