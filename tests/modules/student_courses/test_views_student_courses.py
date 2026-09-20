import pytest
from sqlalchemy import select

from src.modules.users.models import UserRole
from src.modules.students.models import Student
from src.modules.teachers.models import Teacher
from src.modules.student_courses.models import StudentCourse
from src.modules.base.orm_dto import PaginationResponseDTO
from src.modules.student_courses.models_dto import EnrollStudentRequestDTO, StudentCourseResponseDTO

from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO
from tests.modules.student_courses.fixtures.models_dto import CreateStudentCourseFixtureDTO


@pytest.mark.asyncio
async def test_enroll_student_to_course(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
    create_student_course_fixture,
    not_open_session_db,
    session_db,
):
    teacher, t_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))

    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id

    course = await create_course_fixture(CreateCourseFixtureDTO(teacher_id=teacher_table_id))

    dto = EnrollStudentRequestDTO(student_user_id=student.id)

    res = await client_for_tests.post(
        f"/courses/{course.id}/students",
        json=dto.model_dump(exclude_unset=True),
        headers={"Authorization": f"Bearer {t_token}"},
    )

    assert res.status_code == 201
    res_dto = StudentCourseResponseDTO.model_validate(res.json())
    assert res_dto.course_id == course.id


@pytest.mark.asyncio
async def test_unenroll_student_from_course(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
    create_student_course_fixture,
    not_open_session_db,
    session_db,
):
    teacher_user, t_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student_user, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))

    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher_user.id))
        teacher_table_id = t_db.id
        s_db = await session.scalar(select(Student).where(Student.user_id == student_user.id))
        student_table_id = s_db.id

    course = await create_course_fixture(CreateCourseFixtureDTO(teacher_id=teacher_table_id))

    await create_student_course_fixture(CreateStudentCourseFixtureDTO(student_id=student_table_id, course_id=course.id))

    res = await client_for_tests.delete(
        f"/courses/{course.id}/students/{student_user.id}",
        headers={"Authorization": f"Bearer {t_token}"},
    )

    assert res.status_code == 204


@pytest.mark.asyncio
async def test_get_students_for_course(
    client_for_tests,
    create_user_fixture,
    create_course_fixture,
    create_student_course_fixture,
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

    course = await create_course_fixture(CreateCourseFixtureDTO(teacher_id=teacher_table_id))

    await create_student_course_fixture(CreateStudentCourseFixtureDTO(student_id=student_table_id, course_id=course.id))

    res = await client_for_tests.get(
        f"/courses/{course.id}/students",
        headers={"Authorization": f"Bearer {t_token}"},
    )

    assert res.status_code == 200
    res_dto = PaginationResponseDTO[StudentCourseResponseDTO].model_validate(res.json())
    assert res_dto.total == 1
    
    items = res_dto.items
    assert len(items) == 1
    assert items[0].student_id == student_table_id
