import pytest
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helpers.functions import comparison_models
from src.modules.courses.models import AvatarCoursesType
from src.modules.courses.models_dto import CreateCourseDTO
from src.modules.courses.repository import CourseRepository
from src.modules.student_courses.models import StudentCourse
from src.modules.students.models import Student
from src.modules.users.models import UserRole
from src.modules.teachers.models import Teacher
from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


@pytest.mark.asyncio
async def test_add_course_dto(session_db: AsyncSession, create_user_fixture):
    repo = CourseRepository(session=session_db)
    
    user1, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    teacher1_db = (await session_db.execute(select(Teacher).where(Teacher.user_id == user1.id))).scalar_one()

    dto = CreateCourseDTO(
        teacher_id=teacher1_db.id,
        name="Python Base",
        slug="python-base",
        description="Introductory Python course",
        avatar_type=AvatarCoursesType.PYTHON,
        avatar_path=None,
    )

    course = await repo.add_course(dto)
    await session_db.commit()
    await session_db.refresh(course)

    assert course.id is not None
    assert comparison_models(dto, course, keys_not_checked=["id", "created_at", "updated_at"])


@pytest.mark.asyncio
async def test_add_course_dict(session_db: AsyncSession, create_user_fixture):
    repo = CourseRepository(session=session_db)

    user1, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    teacher1_db = (await session_db.execute(select(Teacher).where(Teacher.user_id == user1.id))).scalar_one()

    data = {
        "teacher_id": teacher1_db.id,
        "name": "Math 101",
        "slug": "math-101",
        "description": "Basic math",
        "avatar_type": AvatarCoursesType.MATHEMATICS,
        }

    course = await repo.add_course(data)
    await session_db.commit()
    await session_db.refresh(course)

    assert course.id is not None
    assert comparison_models(data, course, keys_not_checked=["id", "created_at", "updated_at"])


@pytest.mark.asyncio
async def test_get_course_by_id(
    session_db: AsyncSession,
    create_course_fixture,
):
    repo = CourseRepository(session=session_db)

    course = await create_course_fixture(
        CreateCourseFixtureDTO(
            name="Russian",
            slug="russian-lang",
            avatar_type=AvatarCoursesType.RUSSIAN_LANGUAGE,
        )
    )

    fetched = await repo.get_course_by_id(course.id)
    assert fetched is not None
    assert comparison_models(course, fetched)

    not_found = await repo.get_course_by_id(99999)
    assert not_found is None


@pytest.mark.asyncio
async def test_get_course_by_slug(
    session_db: AsyncSession,
    create_course_fixture,
):
    repo = CourseRepository(session=session_db)

    course = await create_course_fixture(
        CreateCourseFixtureDTO(
            name="Algorithms",
            slug="algorithms-pro",
            avatar_type=AvatarCoursesType.CUSTOM,
        )
    )

    fetched = await repo.get_course_by_slug("algorithms-pro")
    assert fetched is not None
    assert comparison_models(course, fetched)

    not_found = await repo.get_course_by_slug("non-existent-slug")
    assert not_found is None


@pytest.mark.asyncio
async def test_get_all_courses(
    session_db: AsyncSession,
    create_course_fixture,
):
    repo = CourseRepository(session=session_db)

    c1 = await create_course_fixture(CreateCourseFixtureDTO(name="Course 1", slug="c-1"))
    c2 = await create_course_fixture(CreateCourseFixtureDTO(name="Course 2", slug="c-2"))
    c3 = await create_course_fixture(CreateCourseFixtureDTO(name="Course 3", slug="c-3"))

    all_courses, _ = await repo.get_all_courses(include_deleted=True)
    assert len(all_courses) == 3

    await repo.update_course(c2.id, {"is_deleted": True})
    await session_db.commit()

    active_courses, _ = await repo.get_all_courses()
    assert len(active_courses) == 2
    assert len(active_courses) > 0

    all_with_deleted, _ = await repo.get_all_courses(include_deleted=True)
    assert len(all_with_deleted) == 3
    deleted_slugs = [c.slug for c in all_with_deleted if c.is_deleted]
    assert "c-2" in deleted_slugs

    paginated, _ = await repo.get_all_courses(limit=2, offset=1)
    assert len(paginated) == 1


@pytest.mark.asyncio
async def test_get_courses_by_student_id(
    session_db: AsyncSession,
    create_user_fixture,
    create_course_fixture,
):
    repo = CourseRepository(session=session_db)

    # Создаем 2 студентов
    user1, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    user2, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))

    student1_db = (await session_db.execute(select(Student).where(Student.user_id == user1.id))).scalar_one()
    student2_db = (await session_db.execute(select(Student).where(Student.user_id == user2.id))).scalar_one()

    # Создаем курсы через фикстуру
    c1 = await create_course_fixture(CreateCourseFixtureDTO(name="Course A", slug="course-a"))
    c2 = await create_course_fixture(CreateCourseFixtureDTO(name="Course B", slug="course-b"))
    c3 = await create_course_fixture(CreateCourseFixtureDTO(name="Course C", slug="course-c"))

    # Привязываем студента 1 к c1 (активен) и c2 (неактивен)
    sc1 = StudentCourse(student_id=student1_db.id, course_id=c1.id)
    sc2 = StudentCourse(student_id=student1_db.id, course_id=c2.id, expires_at=datetime.now(timezone.utc) - timedelta(days=1))
    # Привязываем студента 2 только к c3
    sc3 = StudentCourse(student_id=student2_db.id, course_id=c3.id)

    session_db.add_all([sc1, sc2, sc3])
    await session_db.commit()

    # Получаем все курсы студента 1
    student1_courses, _ = await repo.get_courses_by_student_id(student_id=student1_db.id)
    assert len(student1_courses) == 2
    slugs = {c.slug for c in student1_courses}
    assert slugs == {"course-a", "course-b"}

    # Получаем только активные курсы студента 1
    student1_active, _ = await repo.get_courses_by_student_id(student_id=student1_db.id, only_active=True)
    assert len(student1_active) == 1
    assert student1_active[0].slug == "course-a"

    # Студент 2 видит только свои курсы
    student2_courses, _ = await repo.get_courses_by_student_id(student_id=student2_db.id)
    assert len(student2_courses) == 1
    assert student2_courses[0].slug == "course-c"


@pytest.mark.asyncio
async def test_update_course(
    session_db: AsyncSession,
    create_course_fixture,
):
    repo = CourseRepository(session=session_db)

    course = await create_course_fixture(
        CreateCourseFixtureDTO(name="Old Name", slug="old-slug", description="Old desc")
    )

    updated = await repo.update_course(
        course_id=course.id,
        values={"name": "New Name", "description": "New desc", "is_deleted": True},
    )
    await session_db.commit()

    assert updated is not None
    assert updated.name == "New Name"
    assert updated.description == "New desc"
    assert updated.is_deleted is True

    # Обновление несуществующего курса
    not_found = await repo.update_course(course_id=99999, values={"name": "Test"})
    assert not_found is None


@pytest.mark.asyncio
async def test_delete_course(
    session_db: AsyncSession,
    create_course_fixture,
):
    repo = CourseRepository(session=session_db)

    course = await create_course_fixture(
        CreateCourseFixtureDTO(name="To Delete", slug="to-delete")
    )

    deleted = await repo.delete_course(course_id=course.id)
    await session_db.commit()

    assert deleted is not None
    assert deleted.id == course.id

    # Проверяем, что в базе его больше нет
    check = await repo.get_course_by_id(course.id)
    assert check is None

    # Повторное удаление возвращает None
    deleted_again = await repo.delete_course(course_id=course.id)
    assert deleted_again is None