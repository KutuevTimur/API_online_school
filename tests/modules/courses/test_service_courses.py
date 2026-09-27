from pathlib import Path
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from helpers.functions import comparison_models
from src.modules.courses.exception import CourseNotFound, CourseAlreadyExists
from src.modules.courses.models import AvatarCoursesType, Course
from src.modules.courses.models_dto import (
    CreateCourseDTORequest,
    UpdateCourseDTO,
    UpdateCourseDTORequest,
)
from src.modules.courses.service import CoursesService
from src.modules.student_courses.models import StudentCourse
from src.modules.students.models import Student
from src.modules.users.models import UserRole
from src.modules.teachers.models import Teacher
from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO

@pytest.mark.asyncio
async def test_create_course_success(
    courses_service_fixture: CoursesService,
    session_db: AsyncSession,
    create_user_fixture
):
    user, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    teacher_db = (await session_db.execute(select(Teacher).where(Teacher.user_id == user.id))).scalar_one()

    req = CreateCourseDTORequest(
        name="Python Basics",
        slug="python-basics",
        description="Learn Python from scratch",
    )
    course = await courses_service_fixture.create_course(teacher_id=teacher_db.id, data=req)

    assert course.id is not None
    assert comparison_models(
        req,
        course,
        keys_not_checked=["id", "avatar_type", "avatar_path", "created_at", "updated_at", "teacher_user_id"],
    )
    assert course.avatar_type == AvatarCoursesType.DEFAULT
    assert course.avatar_path is None


@pytest.mark.asyncio
async def test_create_course_duplicate_slug(
    courses_service_fixture: CoursesService,
    create_course_fixture,
    session_db: AsyncSession,
):
    course_dto = await create_course_fixture(
        CreateCourseFixtureDTO(name="Math", slug="math-course")
    )
    res = await session_db.execute(select(Course).where(Course.id == course_dto.id))
    course_obj = res.scalar_one()

    req = CreateCourseDTORequest(name="Math Another", slug="math-course")
    with pytest.raises(CourseAlreadyExists):
        await courses_service_fixture.create_course(teacher_id=course_obj.teacher_id, data=req)


@pytest.mark.asyncio
async def test_get_all_courses_pagination(
    courses_service_fixture: CoursesService,
    create_course_fixture,
):
    for i in range(5):
        await create_course_fixture(
            CreateCourseFixtureDTO(name=f"Course {i}", slug=f"course-{i}")
        )

    all_p1, _ = await courses_service_fixture.get_all_courses(limit=2, offset=0)
    assert len(all_p1) == 2

    all_p2, _ = await courses_service_fixture.get_all_courses(limit=2, offset=2)
    assert len(all_p2) == 2
    assert all_p1[0].id != all_p2[0].id

    active_courses, _ = await courses_service_fixture.get_all_courses()
    assert len(active_courses) == 5


@pytest.mark.asyncio
async def test_get_courses_by_student(
    courses_service_fixture: CoursesService,
    session_db: AsyncSession,
    create_user_fixture,
    create_course_fixture,
):
    user, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    student = (await session_db.execute(select(Student).where(Student.user_id == user.id))).scalar_one()

    c1 = await create_course_fixture(CreateCourseFixtureDTO(name="C1", slug="c1"))
    c2 = await create_course_fixture(CreateCourseFixtureDTO(name="C2", slug="c2"))
    await create_course_fixture(CreateCourseFixtureDTO(name="C3", slug="c3"))

    session_db.add_all([
        StudentCourse(student_id=student.id, course_id=c1.id),
        StudentCourse(student_id=student.id, course_id=c2.id),
    ])
    await session_db.commit()

    student_courses = await courses_service_fixture.get_courses_by_student(
        student_id=student.id,
        limit=10,
        offset=0,
    )
    assert len(student_courses) == 2


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
    assert await courses_service_fixture.get_course_by_id(99999) is None


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
    assert await courses_service_fixture.get_course_by_slug("does-not-exist") is None


@pytest.mark.asyncio
async def test_update_course_success(
    courses_service_fixture: CoursesService,
    create_course_fixture,
    session_db: AsyncSession,
):
    created = await create_course_fixture(
        CreateCourseFixtureDTO(name="Original", slug="orig-slug", description="Orig desc")
    )
    res = await session_db.execute(select(Course).where(Course.id == created.id))
    course_obj = res.scalar_one()

    updated = await courses_service_fixture.update_course(
        course_id=created.id,
        teacher_id=course_obj.teacher_id,
        data=UpdateCourseDTORequest(
            name="Updated Name",
            description="Updated desc",
        ),
    )
    assert updated.name == "Updated Name"
    assert updated.slug == "orig-slug"


@pytest.mark.asyncio
async def test_update_course_duplicate_slug(
    courses_service_fixture: CoursesService,
    create_course_fixture,
    session_db: AsyncSession,
):
    await create_course_fixture(CreateCourseFixtureDTO(name="C1", slug="course-1"))
    c2 = await create_course_fixture(CreateCourseFixtureDTO(name="C2", slug="course-2"))

    res = await session_db.execute(select(Course).where(Course.id == c2.id))
    course_obj = res.scalar_one()

    with pytest.raises(CourseAlreadyExists):
        await courses_service_fixture.update_course(
            course_id=c2.id,
            teacher_id=course_obj.teacher_id,
            data=UpdateCourseDTO(slug="course-1"),
        )


@pytest.mark.asyncio
async def test_update_course_not_found(courses_service_fixture: CoursesService):
    with pytest.raises(CourseNotFound):
        await courses_service_fixture.update_course(
            course_id=99999,
            teacher_id=1,
            data=UpdateCourseDTO(name="Name"),
        )


@pytest.mark.asyncio
async def test_update_avatar(
    courses_service_fixture: CoursesService,
    create_course_fixture,
    create_upload_file_fixture,
    create_image_bytes_fixture,
    session_db: AsyncSession,
):
    created = await create_course_fixture(
        CreateCourseFixtureDTO(name="Avatar Course", slug="avatar-course")
    )
    res = await session_db.execute(select(Course).where(Course.id == created.id))
    course_obj = res.scalar_one()

    upload_file = create_upload_file_fixture(
        create_image_bytes_fixture("PNG", (100, 100), "red"),
        "test_avatar.png",
    )
    updated = await courses_service_fixture.update_avatar(
        course_id=created.id,
        teacher_id=course_obj.teacher_id,
        avatar=upload_file,
    )
    assert updated.avatar_type == AvatarCoursesType.CUSTOM
    assert Path(updated.avatar_path).is_file()

    second_upload = create_upload_file_fixture(
        create_image_bytes_fixture("PNG", (100, 100), "blue"),
        "second.png",
    )
    updated_again = await courses_service_fixture.update_avatar(
        course_id=created.id,
        teacher_id=course_obj.teacher_id,
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
        await courses_service_fixture.update_avatar(course_id=99999, teacher_id=1, avatar=upload_file)


@pytest.mark.asyncio
async def test_delete_course(
    courses_service_fixture: CoursesService,
    create_course_fixture,
    create_upload_file_fixture,
    create_image_bytes_fixture,
    session_db: AsyncSession,
):
    created = await create_course_fixture(
        CreateCourseFixtureDTO(name="To Delete", slug="to-delete")
    )
    res = await session_db.execute(select(Course).where(Course.id == created.id))
    course_obj = res.scalar_one()

    upload_file = create_upload_file_fixture(
        create_image_bytes_fixture("PNG", (100, 100), "red"),
        "del_avatar.png",
    )
    with_avatar = await courses_service_fixture.update_avatar(
        course_id=created.id,
        teacher_id=course_obj.teacher_id,
        avatar=upload_file,
    )
    avatar_file = Path(with_avatar.avatar_path)

    deleted = await courses_service_fixture.delete_course(course_id=created.id, teacher_id=course_obj.teacher_id)
    assert deleted.id == created.id
    assert not avatar_file.exists()

    with pytest.raises(CourseNotFound):
        await courses_service_fixture.delete_course(course_id=created.id, teacher_id=course_obj.teacher_id)
