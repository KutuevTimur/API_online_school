import pytest
from datetime import datetime
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO
from tests.modules.lessons.fixtures.models_dto import CreateLessonFixtureDTO
from sqlalchemy import select
from src.modules.teachers.models import Teacher


@pytest.mark.asyncio
async def test_create_lesson(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
    not_open_session_db,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id

    course_dto = CreateCourseFixtureDTO(name="Physics", slug="phys-101", teacher_id=teacher_table_id)
    course = await create_course_fixture(course_dto)

    payload = {
        "course_id": course.id,
        "title": "Introduction to Physics",
        "topic": "Gravity",
        "description": "Explaining gravity.",
        "scheduled_at": datetime.now().isoformat(),
        "duration_minutes": 90
    }
    
    response = await client_for_tests.post(
        "/lessons",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] > 0
    assert data["title"] == payload["title"]
    assert data["course_id"] == payload["course_id"]
    assert data["teacher_user_id"] == teacher.id


@pytest.mark.asyncio
async def test_get_lessons_with_flags(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    not_open_session_db,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))

    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id

    # Сначала создаем занятия (через фикстуру они привяжутся к новому курсу и нашему учителю)
    lesson1 = await create_lesson_fixture(CreateLessonFixtureDTO(title="L1", teacher_id=teacher_table_id))
    lesson2 = await create_lesson_fixture(CreateLessonFixtureDTO(title="L2", course_id=lesson1.course_id, teacher_id=teacher_table_id))

    response = await client_for_tests.get(
        f"/lessons?course_id={lesson1.course_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert "has_lecture" in data["items"][0]
    assert "has_homework" in data["items"][0]


@pytest.mark.asyncio
async def test_update_lesson(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    not_open_session_db,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id
        
    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id))

    payload = {
        "title": "Updated Title",
        "duration_minutes": 120
    }
    
    response = await client_for_tests.patch(
        f"/lessons/{lesson.id}",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["duration_minutes"] == payload["duration_minutes"]


@pytest.mark.asyncio
async def test_delete_lesson(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    not_open_session_db,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id
        
    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id))

    response = await client_for_tests.delete(
        f"/lessons/{lesson.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200

    # Проверяем, что больше не достается
    get_res = await client_for_tests.get(
        f"/lessons/{lesson.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 404
