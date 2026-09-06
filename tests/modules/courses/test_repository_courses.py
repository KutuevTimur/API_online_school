import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helpers.functions import comparison_models
from src.modules.courses.models import AvatarCoursesType
from src.modules.courses.models_dto import CreateCourseDTO
from src.modules.courses.repository import CourseRepository
from src.modules.student_courses.models import StudentCourses
from src.modules.students.models import Students
from src.modules.users.models import UserRole
from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


@pytest.mark.asyncio
async def test_add_course_dto(session_db: AsyncSession):
    repo = CourseRepository(session=session_db)

    dto = CreateCourseDTO(
        name="Python Base",
        slug="python-base",
        description="Introductory Python course",
        avatar_type=AvatarCoursesType.PYTHON,
        avatar_path=None,
        is_active=True,
    )

    course = await repo.add_course(dto)
    await session_db.commit()
    await session_db.refresh(course)

    assert course.id is not None
    assert comparison_models(dto, course, keys_not_checked=["id", "created_at", "updated_at"])


@pytest.mark.asyncio
async def test_add_course_dict(session_db: AsyncSession):
    repo = CourseRepository(session=session_db)

    data = {
        "name": "Math 101",
        "slug": "math-101",
        "description": "Basic math",
        "avatar_type": AvatarCoursesType.MATHEMATICS,
        "is_active": True,
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

    c1 = await create_course_fixture(CreateCourseFixtureDTO(name="Course 1", slug="c-1", is_active=True))
    c2 = await create_course_fixture(CreateCourseFixtureDTO(name="Course 2", slug="c-2", is_active=False))
    c3 = await create_course_fixture(CreateCourseFixtureDTO(name="Course 3", slug="c-3", is_active=True))

    all_courses = await repo.get_all_courses()
    assert len(all_courses) == 3

    active_courses = await repo.get_all_courses(is_active=True)
    assert len(active_courses) == 2
    assert all(c.is_active for c in active_courses)

    inactive_courses = await repo.get_all_courses(is_active=False)
    assert len(inactive_courses) == 1
    assert inactive_courses[0].slug == "c-2"

    paginated = await repo.get_all_courses(limit=2, offset=1)
    assert len(paginated) == 2


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

    student1_db = (await session_db.execute(select(Students).where(Students.user_id == user1.id))).scalar_one()
    student2_db = (await session_db.execute(select(Students).where(Students.user_id == user2.id))).scalar_one()

    # Создаем курсы через фикстуру
    c1 = await create_course_fixture(CreateCourseFixtureDTO(name="Course A", slug="course-a", is_active=True))
    c2 = await create_course_fixture(CreateCourseFixtureDTO(name="Course B", slug="course-b", is_active=True))
    c3 = await create_course_fixture(CreateCourseFixtureDTO(name="Course C", slug="course-c", is_active=True))

    # Привязываем студента 1 к c1 (активен) и c2 (неактивен)
    sc1 = StudentCourses(student_id=student1_db.id, course_id=c1.id, is_active=True)
    sc2 = StudentCourses(student_id=student1_db.id, course_id=c2.id, is_active=False)
    # Привязываем студента 2 только к c3
    sc3 = StudentCourses(student_id=student2_db.id, course_id=c3.id, is_active=True)

    session_db.add_all([sc1, sc2, sc3])
    await session_db.commit()

    # Получаем все курсы студента 1
    student1_courses = await repo.get_courses_by_student_id(student_id=student1_db.id)
    assert len(student1_courses) == 2
    slugs = {c.slug for c in student1_courses}
    assert slugs == {"course-a", "course-b"}

    # Получаем только активные курсы студента 1
    student1_active = await repo.get_courses_by_student_id(student_id=student1_db.id, only_active=True)
    assert len(student1_active) == 1
    assert student1_active[0].slug == "course-a"

    # Студент 2 видит только свои курсы
    student2_courses = await repo.get_courses_by_student_id(student_id=student2_db.id)
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
        values={"name": "New Name", "description": "New desc", "is_active": False},
    )
    await session_db.commit()

    assert updated is not None
    assert updated.name == "New Name"
    assert updated.description == "New desc"
    assert updated.is_active is False

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
