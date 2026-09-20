import pytest
from src.modules.users.models import UserRole
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.lessons.fixtures.models_dto import CreateLessonFixtureDTO
from tests.modules.lesson_students.fixtures.models_dto import CreateLessonStudentFixtureDTO
from tests.modules.lectures.fixtures.models_dto import CreateLectureFixtureDTO
from sqlalchemy import select
from src.modules.teachers.models import Teacher
from src.modules.students.models import Student
from src.modules.lectures.models_dto import LectureResponseDTO
from src.modules.base.orm_dto import PaginationResponseDTO


@pytest.mark.asyncio
async def test_upload_lecture(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_lesson_student_fixture,
    create_lecture_fixture,
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

    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id))

    await create_lesson_student_fixture(CreateLessonStudentFixtureDTO(lesson_id=lesson.id, student_id=student_table_id))

    form_data = {
        "lesson_id": lesson.id,
        "student_user_id": student.id,
    }
    files = {
        "file": ("lecture1.pdf", b"dummy lecture content", "application/pdf")
    }

    res_upload = await client_for_tests.post(
        "/lectures",
        data=form_data,
        files=files,
        headers={"Authorization": f"Bearer {t_token}"},
    )
    
    assert res_upload.status_code == 201
    res_dto = LectureResponseDTO.model_validate(res_upload.json())
    assert res_dto.pdf_file_name is not None


@pytest.mark.asyncio
async def test_get_lectures_list(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_lesson_student_fixture,
    create_lecture_fixture,
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

    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id))
    
    ls = await create_lesson_student_fixture(CreateLessonStudentFixtureDTO(lesson_id=lesson.id, student_id=student_table_id))
    lecture = await create_lecture_fixture(CreateLectureFixtureDTO(lesson_student_id=ls.id))

    res_list = await client_for_tests.get(
        f"/lectures?lesson_id={lesson.id}&student_user_id={student.id}",
        headers={"Authorization": f"Bearer {t_token}"},
    )
    
    assert res_list.status_code == 200
    res_dto = PaginationResponseDTO[LectureResponseDTO].model_validate(res_list.json())
    assert res_dto.total == 1


@pytest.mark.asyncio
async def test_download_lecture(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_lesson_student_fixture,
    create_lecture_fixture,
    not_open_session_db,
    session_db
):
    teacher, t_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id
        s_db = await session.scalar(select(Student).where(Student.user_id == student.id))
        student_table_id = s_db.id

    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id))

    await create_lesson_student_fixture(CreateLessonStudentFixtureDTO(lesson_id=lesson.id, student_id=student_table_id))

    upload_res = await client_for_tests.post(
        "/lectures",
        data={"lesson_id": lesson.id, "student_user_id": student.id},
        files={"file": ("lecture1.pdf", b"dummy lecture content", "application/pdf")},
        headers={"Authorization": f"Bearer {t_token}"},
    )
    res_dto = LectureResponseDTO.model_validate(upload_res.json())
    lecture_id = res_dto.id

    res_download = await client_for_tests.get(
        f"/lectures/{lecture_id}/file?lesson_id={lesson.id}&student_user_id={student.id}",
        headers={"Authorization": f"Bearer {t_token}"},
    )
    
    assert res_download.status_code == 200
    assert res_download.content == b"dummy lecture content"


@pytest.mark.asyncio
async def test_delete_lecture(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_lesson_student_fixture,
    create_lecture_fixture,
    not_open_session_db,
    session_db,
):
    teacher, t_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id
        student_db = await session.scalar(select(Student).where(Student.user_id == student.id))
        s_table_id = student_db.id

    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id))

    ls = await create_lesson_student_fixture(CreateLessonStudentFixtureDTO(lesson_id=lesson.id, student_id=s_table_id))
    lecture = await create_lecture_fixture(CreateLectureFixtureDTO(lesson_student_id=ls.id))

    res_del = await client_for_tests.delete(
        f"/lectures/{lecture.id}?lesson_id={lesson.id}&student_user_id={student.id}",
        headers={"Authorization": f"Bearer {t_token}"},
    )
    
    assert res_del.status_code == 200
    
    res_list_after = await client_for_tests.get(
        f"/lectures?lesson_id={lesson.id}&student_user_id={student.id}",
        headers={"Authorization": f"Bearer {t_token}"},
    )
    res_dto_after = PaginationResponseDTO[LectureResponseDTO].model_validate(res_list_after.json())
    assert res_dto_after.total == 0
