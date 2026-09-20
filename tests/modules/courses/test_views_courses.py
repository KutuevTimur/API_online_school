import io
import pytest
from sqlalchemy import select
from src.modules.teachers.models import Teacher
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.courses.models import Course, AvatarCoursesType
from src.modules.courses.models_dto import CreateCourseDTORequest, UpdateCourseDTORequest, CoursesResponseDTO
from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.path_builder import PathBuilder
from src.modules.student_courses.models import StudentCourse
from src.modules.students.models import Student
from src.modules.users.models import UserRole
from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


# =====================================================================
# 1. GET /courses
# =====================================================================

@pytest.mark.asyncio
async def test_get_courses_as_teacher(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))

    c1 = await create_course_fixture(CreateCourseFixtureDTO(name="Python 1", slug="py-1", is_active=True))
    c2 = await create_course_fixture(CreateCourseFixtureDTO(name="Python 2", slug="py-2", is_active=False))

    response = await client_for_tests.get(
        "/courses",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    res_dto = PaginationResponseDTO[CoursesResponseDTO].model_validate(response.json())
    assert len(res_dto.items) >= 2
    slugs = [c.slug for c in res_dto.items]
    assert c1.slug in slugs
    assert c2.slug in slugs

    # _????????? alias /courses
    alias_res = await client_for_tests.get(
        "/courses",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert alias_res.status_code == 200


@pytest.mark.asyncio
async def test_get_courses_as_teacher_filters(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))

    await create_course_fixture(CreateCourseFixtureDTO(name="Active 1", slug="act-1", is_active=True))
    await create_course_fixture(CreateCourseFixtureDTO(name="Inactive 1", slug="inact-1", is_active=False))

    # is_active filter
    res_active = await client_for_tests.get(
        "/courses?is_active=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_active.status_code == 200
    res_dto = PaginationResponseDTO[CoursesResponseDTO].model_validate(res_active.json())
    assert all(c.is_active is True for c in res_dto.items)

    # teacher_id filter (_?????????? +>????>?: ??? >???''??? ??????>? >???'??? ???>'? ????>?)
    res_teacher = await client_for_tests.get(
        "/courses?teacher_user_id=9999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_teacher.status_code == 200
    res_teach_dto = PaginationResponseDTO[CoursesResponseDTO].model_validate(res_teacher.json())
    assert res_teach_dto.items == []


@pytest.mark.asyncio
async def test_get_courses_as_student_only_enrolled(
    client_for_tests,
    session_db: AsyncSession,
    create_user_fixture,
    create_course_fixture,
):
    user_student, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    student_res = await session_db.execute(select(Student).where(Student.user_id == user_student.id))
    student = student_res.scalar_one()

    c_enrolled = await create_course_fixture(CreateCourseFixtureDTO(name="Enrolled Course", slug="enrolled", is_active=True))
    c_not_enrolled = await create_course_fixture(CreateCourseFixtureDTO(name="Other Course", slug="other", is_active=True))
    c_inactive = await create_course_fixture(CreateCourseFixtureDTO(name="Inactive Course", slug="inactive-enrolled", is_active=False))

    # _???'>?"??? ?'????'  c_enrolled ? c_inactive
    session_db.add_all([
        StudentCourse(student_id=student.id, course_id=c_enrolled.id, is_active=True),
        StudentCourse(student_id=student.id, course_id=c_inactive.id, is_active=True),
    ])
    await session_db.commit()

    response = await client_for_tests.get(
        "/courses",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    res_dto = PaginationResponseDTO[CoursesResponseDTO].model_validate(response.json())
    slugs = {c.slug for c in res_dto.items}
    assert c_enrolled.slug in slugs
    assert c_not_enrolled.slug not in slugs
    # _+?<?>"??? ???  ?'????'  ?? >???'???
    assert c_inactive.slug not in slugs


@pytest.mark.asyncio
async def test_get_courses_unauthorized(client_for_tests):
    response = await client_for_tests.get("/courses")
    assert response.status_code == 401


# =====================================================================
# 2. GET /courses/{course_id}
# =====================================================================

@pytest.mark.asyncio
async def test_get_course_by_id_as_teacher(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    course = await create_course_fixture(CreateCourseFixtureDTO(name="Any Course", slug="any-course"))

    response = await client_for_tests.get(
        f"/courses/{course.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    res_dto = CoursesResponseDTO.model_validate(response.json())
    assert res_dto.id == course.id


@pytest.mark.asyncio
async def test_get_course_by_id_as_student_allowed(
    client_for_tests,
    session_db: AsyncSession,
    create_user_fixture,
    create_course_fixture,
):
    user_student, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    student_res = await session_db.execute(select(Student).where(Student.user_id == user_student.id))
    student = student_res.scalar_one()

    course = await create_course_fixture(CreateCourseFixtureDTO(name="Allowed Course", slug="allowed-course", is_active=True))
    session_db.add(StudentCourse(student_id=student.id, course_id=course.id, is_active=True))
    await session_db.commit()

    response = await client_for_tests.get(
        f"/courses/{course.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    res_dto = CoursesResponseDTO.model_validate(response.json())
    assert res_dto.id == course.id


@pytest.mark.asyncio
async def test_get_course_by_id_as_student_forbidden_not_enrolled(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
):
    user_student, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    course = await create_course_fixture(CreateCourseFixtureDTO(name="Secret Course", slug="secret-course"))

    response = await client_for_tests.get(
        f"/courses/{course.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Not permission"}


@pytest.mark.asyncio
async def test_get_course_by_id_not_found(
    client_for_tests,
    create_user_fixture,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))

    response = await client_for_tests.get(
        "/courses/99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Not found data"}


# =====================================================================
# 3. POST /courses
# =====================================================================

@pytest.mark.asyncio
async def test_create_course_by_teacher(
    client_for_tests,
    create_user_fixture,
    session_db: AsyncSession,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))

    dto = CreateCourseDTORequest(
        name="New FastApi Course",
        slug="new-fastapi-course",
        description="Detailed description",
        is_active=True,
    )
    response = await client_for_tests.post(
        "/courses",
        headers={"Authorization": f"Bearer {token}"},
        json=dto.model_dump(),
    )
    assert response.status_code == 201
    res_dto = CoursesResponseDTO.model_validate(response.json())
    assert res_dto.name == "New FastApi Course"
    assert res_dto.slug == "new-fastapi-course"
    assert res_dto.avatar_type == AvatarCoursesType.DEFAULT

    # _?????????  ""
    res_db = await session_db.execute(select(Course).where(Course.slug == "new-fastapi-course"))
    course_db = res_db.scalar_one_or_none()
    assert course_db is not None
    assert course_db.name == "New FastApi Course"


@pytest.mark.asyncio
async def test_create_course_forbidden_for_student(
    client_for_tests,
    create_user_fixture,
):
    student, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))

    dto = CreateCourseDTORequest(name="Hack", slug="hack-course")
    response = await client_for_tests.post(
        "/courses",
        headers={"Authorization": f"Bearer {token}"},
        json=dto.model_dump(),
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Not permission"}


@pytest.mark.asyncio
async def test_create_course_duplicate_slug(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    await create_course_fixture(CreateCourseFixtureDTO(name="First", slug="existing-slug"))

    response = await client_for_tests.post(
        "/courses",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Second", "slug": "existing-slug"},
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"].lower()


# =====================================================================
# 4. PATCH /courses/{course_id}
# =====================================================================

@pytest.mark.asyncio
async def test_update_course_by_teacher(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
    session_db: AsyncSession,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    res_t = await session_db.execute(select(Teacher).where(Teacher.user_id == teacher.id))
    teacher_db = res_t.scalar_one()
    course = await create_course_fixture(CreateCourseFixtureDTO(teacher_id=teacher_db.id, name="Old Name", slug="old-slug"))

    dto = UpdateCourseDTORequest(
        name="Updated Name",
        description="Updated Description",
        is_active=False,
    )
    response = await client_for_tests.patch(
        f"/courses/{course.id}",
        headers={"Authorization": f"Bearer {token}"},
        json=dto.model_dump(exclude_unset=True),
    )
    assert response.status_code == 200
    res_dto = CoursesResponseDTO.model_validate(response.json())
    assert res_dto.name == "Updated Name"
    assert res_dto.description == "Updated Description"
    assert res_dto.is_active is False

    # _?????????  ""
    res_db = await session_db.execute(select(Course).where(Course.id == course.id))
    db_course = res_db.scalar_one()
    assert db_course.name == "Updated Name"
    assert db_course.is_active is False


@pytest.mark.asyncio
async def test_update_course_forbidden_for_student(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
):
    student, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    course = await create_course_fixture(CreateCourseFixtureDTO(name="Name", slug="slug-for-upd"))

    response = await client_for_tests.patch(
        f"/courses/{course.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Hacked"},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Not permission"}


# =====================================================================
# 5. PATCH /courses/{course_id}/avatar
# =====================================================================

@pytest.mark.asyncio
async def test_update_avatar_by_teacher(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
    create_image_bytes_fixture,
    session_db: AsyncSession,
    config_fix,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    res_t = await session_db.execute(select(Teacher).where(Teacher.user_id == teacher.id))
    teacher_db = res_t.scalar_one()
    course = await create_course_fixture(CreateCourseFixtureDTO(teacher_id=teacher_db.id, name="Avatar C", slug="avatar-c"))

    image_bytes = create_image_bytes_fixture("PNG", (400, 400), "green")
    response = await client_for_tests.patch(
        f"/courses/{course.id}/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"avatar": ("cover.png", io.BytesIO(image_bytes), "image/png")},
    )

    assert response.status_code == 200
    assert response.content == image_bytes
    assert response.headers.get("content-type") == "image/png"
    assert response.headers.get("content-disposition") == 'inline; filename="cover.png"'

    # _????????? ?"??>???? ??+?  ????
    avatar_file = PathBuilder(config=config_fix).get_avatar_course(course.id)
    assert avatar_file.is_file()

    # _????????? >?>?"???? <?>???  ""
    res_db = await session_db.execute(select(Course).where(Course.id == course.id))
    db_course = res_db.scalar_one()
    assert db_course.avatar_type == AvatarCoursesType.CUSTOM
    assert db_course.avatar_path == str(avatar_file)


@pytest.mark.asyncio
async def test_update_avatar_forbidden_for_student(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
    create_image_bytes_fixture,
):
    student, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    course = await create_course_fixture(CreateCourseFixtureDTO(name="C", slug="c-stud-avatar"))

    image_bytes = create_image_bytes_fixture("PNG", (100, 100))
    response = await client_for_tests.patch(
        f"/courses/{course.id}/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"avatar": ("cover.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Not permission"}


# =====================================================================
# 6. DELETE /courses/{course_id}
# =====================================================================

@pytest.mark.asyncio
async def test_soft_delete_course_by_teacher_and_reuse_slug(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
    session_db: AsyncSession,
):
    """
    _????????? <'?+> ?> "?'??:
    1. _??? ?' >"?is_active = False.
    2. _+?+?"+?:  slug >?? ?"????? (> "+?? __deleted__).
    3. _>?' "+ ? ?> >+> ????  '+ ?  slug ?" :? >?'> ? ?"??+  ? ?>"?" ?>++ ?' ???+?"+?>'?!
    """
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    res_t = await session_db.execute(select(Teacher).where(Teacher.user_id == teacher.id))
    teacher_db = res_t.scalar_one()
    orig_slug = "unique-course-slug"
    course = await create_course_fixture(CreateCourseFixtureDTO(teacher_id=teacher_db.id, name="To Soft Delete", slug=orig_slug, is_active=True))

    del_response = await client_for_tests.delete(
        f"/courses/{course.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_response.status_code == 200
    res_dto = CoursesResponseDTO.model_validate(del_response.json())
    assert res_dto.id == course.id
    assert res_dto.is_active is False
    assert res_dto.slug.startswith(orig_slug)
    assert "__deleted__" in res_dto.slug

    # _?????????  "": ' ?"?? ? +"' ?, > ?>+'??? > "?
    res_db = await session_db.execute(select(Course).where(Course.id == course.id))
    db_course = res_db.scalar_one_or_none()
    assert db_course is not None
    assert db_course.is_active is False

    # _? ?">? ?> "?'?? >??'?? 404 Not Found
    del_again = await client_for_tests.delete(
        f"/courses/{course.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_again.status_code == 404

    # _>?' '+ ? ?>? ???  _ _ _ slug - ??+?"+?>' ?" ) "' "?!
    create_res = await client_for_tests.post(
        "/courses",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Recreated Course", "slug": orig_slug},
    )
    assert create_res.status_code == 201
    create_dto = CoursesResponseDTO.model_validate(create_res.json())
    assert create_dto.slug == orig_slug


@pytest.mark.asyncio
async def test_hard_delete_course_by_teacher(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
    create_image_bytes_fixture,
    session_db: AsyncSession,
    config_fix,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    res_t = await session_db.execute(select(Teacher).where(Teacher.user_id == teacher.id))
    teacher_db = res_t.scalar_one()
    course = await create_course_fixture(CreateCourseFixtureDTO(teacher_id=teacher_db.id, name="Hard Delete Me", slug="hard-del-course"))

    # _??' '  ?'?
    image_bytes = create_image_bytes_fixture("PNG", (200, 200))
    avatar_res = await client_for_tests.patch(
        f"/courses/{course.id}/avatar",
        headers={"Authorization": f"Bearer {token}"},
        files={"avatar": ("avatar.png", io.BytesIO(image_bytes), "image/png")},
    )
    assert avatar_res.status_code == 200
    avatar_path = PathBuilder(config=config_fix).get_avatar_course(course.id)
    assert avatar_path.is_file()

    # _?-??+' ?> "?'?? ? ?) ?hard=true
    del_res = await client_for_tests.delete(
        f"/courses/{course.id}?hard=true",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 200

    # _?? ?' ? ?> 
    assert not avatar_path.exists()

    # _' ?"?? ?> "?  1  ""
    res_db = await session_db.execute(select(Course).where(Course.id == course.id))
    assert res_db.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_course_forbidden_for_student(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
):
    student, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    course = await create_course_fixture(CreateCourseFixtureDTO(name="C", slug="student-cannot-del"))

    response = await client_for_tests.delete(
        f"/courses/{course.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Not permission"}
