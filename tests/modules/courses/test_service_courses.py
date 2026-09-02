from pathlib import Path
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helpers.functions import comparison_models
from src.modules.courses.exception import CourseNotFound, CourseAlreadyExists
from src.modules.courses.models import AvatarCoursesType
from src.modules.courses.models_dto import (
    CreateCourseDTORequest,
    UpdateCourseDTO,
    UpdateCourseDTORequest,
)
from src.modules.courses.service import CoursesService
from src.modules.student_courses.models import StudentCourses
from src.modules.students.models import Students
from src.modules.users.models import UserRole
from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


@pytest.mark.asyncio
async def test_create_course_success(courses_service_fixture: CoursesService):
    req = CreateCourseDTORequest(
        name="Python Basics",
        slug="python-basics",
        description="Learn Python from scratch",
        is_active=True,
    )
    course = await courses_service_fixture.create_course(req)

    assert course.id is not None
    assert comparison_models(
        req,
        course,
        keys_not_checked=["id", "avatar_type", "avatar_path", "created_at", "updated_at"],
    )
    assert course.avatar_type == AvatarCoursesType.DEFAULT
    assert course.avatar_path is None


@pytest.mark.asyncio
async def test_create_course_duplicate_slug(
    courses_service_fixture: CoursesService,
    create_course_fixture,
):
    await create_course_fixture(
        CreateCourseFixtureDTO(name="Math", slug="math-course")
    )

    req = CreateCourseDTORequest(name="Math Another", slug="math-course")
    with pytest.raises(CourseAlreadyExists):
        await courses_service_fixture.create_course(req)


@pytest.mark.asyncio
async def test_get_all_courses_pagination(
    courses_service_fixture: CoursesService,
    create_course_fixture,
):
    for i in range(5):
        await create_course_fixture(
            CreateCourseFixtureDTO(name=f"Course {i}", slug=f"course-{i}", is_active=(i % 2 == 0))
        )

    # limit & offset
    all_p1 = await courses_service_fixture.get_all_courses(limit=2, offset=0)
    assert len(all_p1) == 2

    all_p2 = await courses_service_fixture.get_all_courses(limit=2, offset=2)
    assert len(all_p2) == 2
    assert all_p1[0].id != all_p2[0].id

    # is_active filter
    active_courses = await courses_service_fixture.get_all_courses(is_active=True)
    assert len(active_courses) == 3
    assert all(c.is_active for c in active_courses)


@pytest.mark.asyncio
async def test_get_courses_by_student(
    courses_service_fixture: CoursesService,
    session_db: AsyncSession,
    create_user_fixture,
    create_course_fixture,
):
    user, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    student = (await session_db.execute(select(Students).where(Students.user_id == user.id))).scalar_one()

    c1 = await create_course_fixture(CreateCourseFixtureDTO(name="C1", slug="c1"))
    c2 = await create_course_fixture(CreateCourseFixtureDTO(name="C2", slug="c2"))
    await create_course_fixture(CreateCourseFixtureDTO(name="C3", slug="c3"))

    # Привязываем только к c1 и c2
    session_db.add_all([
        StudentCourses(student_id=student.id, course_id=c1.id, is_active=True),
        StudentCourses(student_id=student.id, course_id=c2.id, is_active=True),
    ])
    await session_db.commit()

    student_courses = await courses_service_fixture.get_courses(
        student_id=student.id,
        limit=10,
        offset=0,
    )
    assert len(student_courses) == 2
    slugs = {c.slug for c in student_courses}
    assert slugs == {"c1", "c2"}


@pytest.mark.asyncio
async def test_get_course_by_id(
    courses_service_fixture: CoursesService,
    create_course_fixture,
):
    created = await create_course_fixture(
        CreateCourseFixtureDTO(name="Target Course", slug="target-course")
    )

    found = await courses_service_fixture.get_course_by_id(created.id)
    assert found is not None
    assert comparison_models(created, found)

    not_found = await courses_service_fixture.get_course_by_id(99999)
    assert not_found is None


@pytest.mark.asyncio
async def test_get_course_by_slug(
    courses_service_fixture: CoursesService,
    create_course_fixture,
):
    created = await create_course_fixture(
        CreateCourseFixtureDTO(name="Slug Test", slug="slug-test")
    )

    found = await courses_service_fixture.get_course_by_slug("slug-test")
    assert found is not None
    assert comparison_models(created, found)

    not_found = await courses_service_fixture.get_course_by_slug("does-not-exist")
    assert not_found is None


@pytest.mark.asyncio
async def test_update_course_success(
    courses_service_fixture: CoursesService,
    create_course_fixture,
):
    created = await create_course_fixture(
        CreateCourseFixtureDTO(name="Original", slug="orig-slug", description="Orig desc")
    )

    updated = await courses_service_fixture.update_course(
        course_id=created.id,
        data=UpdateCourseDTORequest(
            name="Updated Name",
            description="Updated desc",
            is_active=False,
        ),
    )

    assert updated.name == "Updated Name"
    assert updated.description == "Updated desc"
    assert updated.is_active is False
    assert updated.slug == "orig-slug"


@pytest.mark.asyncio
async def test_update_course_duplicate_slug(
    courses_service_fixture: CoursesService,
    create_course_fixture,
):
    await create_course_fixture(CreateCourseFixtureDTO(name="C1", slug="course-1"))
    c2 = await create_course_fixture(CreateCourseFixtureDTO(name="C2", slug="course-2"))

    with pytest.raises(CourseAlreadyExists):
        await courses_service_fixture.update_course(
            course_id=c2.id,
            data=UpdateCourseDTO(slug="course-1"),
        )


@pytest.mark.asyncio
async def test_update_course_not_found(courses_service_fixture: CoursesService):
    with pytest.raises(CourseNotFound):
        await courses_service_fixture.update_course(
            course_id=99999,
            data=UpdateCourseDTO(name="Name"),
        )


@pytest.mark.asyncio
async def test_update_avatar(
    courses_service_fixture: CoursesService,
    create_course_fixture,
    create_upload_file_fixture,
    create_image_bytes_fixture,
):
    created = await create_course_fixture(
        CreateCourseFixtureDTO(name="Avatar Course", slug="avatar-course")
    )

    upload_file = create_upload_file_fixture(
        create_image_bytes_fixture("PNG", (100, 100), "red"),
        "test_avatar.png",
    )
    updated = await courses_service_fixture.update_avatar(
        course_id=created.id,
        avatar=upload_file,
    )

    assert updated.avatar_type == AvatarCoursesType.CUSTOM
    assert updated.avatar_path is not None
    assert Path(updated.avatar_path).is_file()

    # Повторное обновление заменяет существующую аватарку
    second_upload = create_upload_file_fixture(
        create_image_bytes_fixture("PNG", (100, 100), "blue"),
        "second.png",
    )
    updated_again = await courses_service_fixture.update_avatar(
        course_id=created.id,
        avatar=second_upload,
    )
    assert updated_again.avatar_type == AvatarCoursesType.CUSTOM
    assert Path(updated_again.avatar_path).is_file()


@pytest.mark.asyncio
async def test_update_avatar_course_not_found(
    courses_service_fixture: CoursesService,
    create_upload_file_fixture,
    create_image_bytes_fixture,
):
    upload_file = create_upload_file_fixture(
        create_image_bytes_fixture("PNG", (100, 100), "red"),
        "avatar.png",
    )
    with pytest.raises(CourseNotFound):
        await courses_service_fixture.update_avatar(course_id=99999, avatar=upload_file)


@pytest.mark.asyncio
async def test_delete_course(
    courses_service_fixture: CoursesService,
    create_course_fixture,
    create_upload_file_fixture,
    create_image_bytes_fixture,
):
    created = await create_course_fixture(
        CreateCourseFixtureDTO(name="To Delete", slug="to-delete")
    )

    # Прикрепим аватарку
    upload_file = create_upload_file_fixture(
        create_image_bytes_fixture("PNG", (100, 100), "red"),
        "del_avatar.png",
    )
    with_avatar = await courses_service_fixture.update_avatar(
        course_id=created.id,
        avatar=upload_file,
    )
    avatar_file = Path(with_avatar.avatar_path)
    assert avatar_file.is_file()

    deleted = await courses_service_fixture.delete_course(course_id=created.id)
    assert deleted.id == created.id

    # Проверяем, что курс удалён из БД и файл аватарки удалён с диска
    assert not avatar_file.exists()
    assert await courses_service_fixture.get_course_by_id(created.id) is None

    # Повторное удаление вызывает CourseNotFound
    with pytest.raises(CourseNotFound):
        await courses_service_fixture.delete_course(course_id=created.id)
