import pytest
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.lessons.fixtures.models_dto import CreateLessonFixtureDTO
from tests.modules.lesson_students.fixtures.models_dto import CreateLessonStudentFixtureDTO
from sqlalchemy import select
from src.modules.teachers.models import Teacher
from src.modules.students.models import Student
from src.modules.lesson_students.models import LessonStudent
from src.modules.lesson_students.models_dto import AddStudentToLessonRequestDTO


@pytest.mark.asyncio
async def test_add_student_to_lesson(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_course_fixture,
    create_lesson_student_fixture,
    not_open_session_db,
    session_db,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, student_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id

    from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO
    course = await create_course_fixture(CreateCourseFixtureDTO(teacher_id=teacher_table_id))
    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id, course_id=course.id))

    from src.modules.teacher_students.models import TeacherStudent
    from src.modules.student_courses.models import StudentCourse
    student_pk = await session_db.scalar(select(Student.id).where(Student.user_id == student.id))
    session_db.add(TeacherStudent(teacher_id=teacher_table_id, student_id=student_pk))
    session_db.add(StudentCourse(course_id=course.id, student_id=student_pk))
    await session_db.commit()

    add_dto = AddStudentToLessonRequestDTO(student_user_id=student.id)
    response = await client_for_tests.post(
        f"/lessons/{lesson.id}/students",
        json=add_dto.model_dump(),
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert response.status_code == 201
    
    session_db.expire_all()
    get_res = await client_for_tests.get(
        f"/lessons/{lesson.id}",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert get_res.status_code == 200


@pytest.mark.asyncio
async def test_remove_student_from_lesson(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_course_fixture,
    create_lesson_student_fixture,
    not_open_session_db,
    session_db,
):
    teacher, token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, student_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id
        s_db = await session.scalar(select(Student).where(Student.user_id == student.id))
        student_table_id = s_db.id

    from tests.modules.courses.fixtures.models_dto import CreateCourseFixtureDTO
    course = await create_course_fixture(CreateCourseFixtureDTO(teacher_id=teacher_table_id))
    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id, course_id=course.id))

    await create_lesson_student_fixture(CreateLessonStudentFixtureDTO(lesson_id=lesson.id, student_id=student_table_id))

    del_res = await client_for_tests.delete(
        f"/lessons/{lesson.id}/students/{student.id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    
    assert del_res.status_code == 200

    async with not_open_session_db() as local_session:
        ls_db = await local_session.scalar(select(LessonStudent).where(
            LessonStudent.lesson_id == lesson.id,
            LessonStudent.student_id == student_table_id,
        ))
        assert ls_db is not None and ls_db.access_ended_at is not None
