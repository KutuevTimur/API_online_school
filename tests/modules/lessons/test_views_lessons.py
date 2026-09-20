import pytest
from datetime import datetime, timezone
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO
from tests.modules.lessons.fixtures.models_dto import CreateLessonFixtureDTO
from sqlalchemy import select
from src.modules.teachers.models import Teacher
from src.modules.lessons.models_dto import CreateLessonRequestDTO, UpdateLessonRequestDTO, LessonResponseDTO
from src.modules.base.orm_dto import PaginationResponseDTO


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

    create_dto = CreateLessonRequestDTO(
        course_id=course.id,
        title="Introduction to Physics",
        topic="Gravity",
        description="Explaining gravity.",
        scheduled_at=datetime.now(timezone.utc),
        duration_minutes=90
    )
    
    response = await client_for_tests.post(
        "/lessons",
        json=create_dto.model_dump(mode="json"),
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 201
    res_dto = LessonResponseDTO.model_validate(response.json())
    assert res_dto.id > 0
    assert res_dto.title == create_dto.title
    assert res_dto.course_id == create_dto.course_id
    assert res_dto.teacher_user_id == teacher.id


@pytest.mark.asyncio
async def test_get_lessons(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    not_open_session_db,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))

    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id

    lesson1 = await create_lesson_fixture(CreateLessonFixtureDTO(title="L1", teacher_id=teacher_table_id))
    await create_lesson_fixture(CreateLessonFixtureDTO(title="L2", course_id=lesson1.course_id, teacher_id=teacher_table_id))

    response = await client_for_tests.get(
        f"/lessons?course_id={lesson1.course_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    res_dto = PaginationResponseDTO[LessonResponseDTO].model_validate(response.json())
    assert res_dto.total == 2
    assert res_dto.items[0].has_lecture is not None
    assert res_dto.items[0].has_homework is not None


@pytest.mark.asyncio
async def test_get_lesson_by_id(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    not_open_session_db,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id

    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(title="Get Me", teacher_id=teacher_table_id))

    response = await client_for_tests.get(
        f"/lessons/{lesson.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    res_dto = LessonResponseDTO.model_validate(response.json())
    assert res_dto.title == "Get Me"


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

    update_dto = UpdateLessonRequestDTO(
        title="Updated Title",
        duration_minutes=120
    )
    
    response = await client_for_tests.patch(
        f"/lessons/{lesson.id}",
        json=update_dto.model_dump(exclude_unset=True),
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 200
    res_dto = LessonResponseDTO.model_validate(response.json())
    assert res_dto.title == update_dto.title
    assert res_dto.duration_minutes == update_dto.duration_minutes


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

    get_res = await client_for_tests.get(
        f"/lessons/{lesson.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 404
