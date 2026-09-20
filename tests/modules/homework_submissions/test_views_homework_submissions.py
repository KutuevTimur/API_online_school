import pytest
from src.modules.users.models import UserRole
from src.modules.homework_submissions.models import HomeworkSubmissionStatus
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO
from tests.modules.lessons.fixtures.models_dto import CreateLessonFixtureDTO
from tests.modules.lesson_students.fixtures.models_dto import CreateLessonStudentFixtureDTO
from tests.modules.homeworks.fixtures.models_dto import CreateHomeworkFixtureDTO
from tests.modules.homework_submissions.fixtures.models_dto import CreateHomeworkSubmissionFixtureDTO
from sqlalchemy import select
from src.modules.teachers.models import Teacher
from src.modules.students.models import Student
from src.modules.homework_submissions.models_dto import (
    UpdateSubmissionStudentRequestDTO,
    UpdateSubmissionTeacherRequestDTO,
)


@pytest.mark.asyncio
async def test_create_homework_submission(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_lesson_student_fixture,
    create_homework_fixture,
    create_homework_submission_fixture,
    not_open_session_db,
    session_db,
):
    teacher, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, s_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id
        s_db = await session.scalar(select(Student).where(Student.user_id == student.id))
        student_table_id = s_db.id

    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id))

    ls = await create_lesson_student_fixture(CreateLessonStudentFixtureDTO(lesson_id=lesson.id, student_id=student_table_id))
    homework = await create_homework_fixture(CreateHomeworkFixtureDTO(lesson_student_id=ls.id))
    
    sub_data = {
        "text_content": "Here is my homework response!"
    }
    res_sub = await client_for_tests.post(
        f"/homeworks/{homework.id}/submissions",
        data=sub_data,
        headers={"Authorization": f"Bearer {s_token}"},
    )
    
    assert res_sub.status_code == 201
    assert res_sub.json()["status"] == HomeworkSubmissionStatus.DRAFT.value


@pytest.mark.asyncio
async def test_get_homework_submissions(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_lesson_student_fixture,
    create_homework_fixture,
    create_homework_submission_fixture,
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
    homework = await create_homework_fixture(CreateHomeworkFixtureDTO(lesson_student_id=ls.id))

    submission = await create_homework_submission_fixture(
        CreateHomeworkSubmissionFixtureDTO(homework_id=homework.id, status=HomeworkSubmissionStatus.DRAFT)
    )

    res_get_all = await client_for_tests.get(
        f"/homeworks/{homework.id}/submissions",
        headers={"Authorization": f"Bearer {t_token}"},
    )
    
    assert res_get_all.status_code == 200
    assert res_get_all.json()["total"] == 1


@pytest.mark.asyncio
async def test_get_homework_submission_by_id(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_lesson_student_fixture,
    create_homework_fixture,
    create_homework_submission_fixture,
    not_open_session_db,
    session_db,
):
    teacher, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, s_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id
        s_db = await session.scalar(select(Student).where(Student.user_id == student.id))
        student_table_id = s_db.id

    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id))

    ls = await create_lesson_student_fixture(CreateLessonStudentFixtureDTO(lesson_id=lesson.id, student_id=student_table_id))
    homework = await create_homework_fixture(CreateHomeworkFixtureDTO(lesson_student_id=ls.id))

    submission = await create_homework_submission_fixture(
        CreateHomeworkSubmissionFixtureDTO(homework_id=homework.id,status=HomeworkSubmissionStatus.DRAFT)
    )

    res_get_one = await client_for_tests.get(
        f"/submissions/{submission.id}?homework_id={homework.id}",
        headers={"Authorization": f"Bearer {s_token}"}
    )
    
    assert res_get_one.status_code == 200
    assert res_get_one.json()["id"] == submission.id


@pytest.mark.asyncio
async def test_update_homework_submission_student(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_lesson_student_fixture,
    create_homework_fixture,
    create_homework_submission_fixture,
    not_open_session_db,
    session_db,
):
    teacher, _ = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.TEACHER))
    student, s_token = await create_user_fixture(CreateUserFixtureDTO(role=UserRole.STUDENT))
    
    async with not_open_session_db() as session:
        t_db = await session.scalar(select(Teacher).where(Teacher.user_id == teacher.id))
        teacher_table_id = t_db.id
        s_db = await session.scalar(select(Student).where(Student.user_id == student.id))
        student_table_id = s_db.id

    lesson = await create_lesson_fixture(CreateLessonFixtureDTO(teacher_id=teacher_table_id))

    ls = await create_lesson_student_fixture(CreateLessonStudentFixtureDTO(lesson_id=lesson.id, student_id=student_table_id))
    homework = await create_homework_fixture(CreateHomeworkFixtureDTO(lesson_student_id=ls.id))

    submission = await create_homework_submission_fixture(
        CreateHomeworkSubmissionFixtureDTO(homework_id=homework.id, status=HomeworkSubmissionStatus.DRAFT)
    )

    update_dto = UpdateSubmissionStudentRequestDTO(text_content="Updated response")
    
    res_update_s = await client_for_tests.patch(
        f"/submissions/{submission.id}/student?homework_id={homework.id}",
        data=update_dto.model_dump(exclude_unset=True),
        headers={"Authorization": f"Bearer {s_token}"},
    )
    
    assert res_update_s.status_code == 200
    assert res_update_s.json()["text_content"] == "Updated response"


@pytest.mark.asyncio
async def test_update_homework_submission_teacher(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_lesson_student_fixture,
    create_homework_fixture,
    create_homework_submission_fixture,
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
    homework = await create_homework_fixture(CreateHomeworkFixtureDTO(lesson_student_id=ls.id))

    submission = await create_homework_submission_fixture(
        CreateHomeworkSubmissionFixtureDTO(homework_id=homework.id, status=HomeworkSubmissionStatus.SUBMITTED)
    )

    update_dto = UpdateSubmissionTeacherRequestDTO(
        status=HomeworkSubmissionStatus.CHECKED,
        grade=5.0,
        teacher_comment="Good job"
    )
    
    res_update_t = await client_for_tests.patch(
        f"/submissions/{submission.id}/teacher?homework_id={homework.id}",
        json=update_dto.model_dump(mode="json", exclude_unset=True),
        headers={"Authorization": f"Bearer {t_token}"},
    )
    
    assert res_update_t.status_code == 200
    assert res_update_t.json()["status"] == HomeworkSubmissionStatus.CHECKED.value
    assert res_update_t.json()["grade"] == 5.0


@pytest.mark.asyncio
async def test_delete_homework_submission(
    client_for_tests,
    create_user_fixture,
    create_lesson_fixture,
    create_lesson_student_fixture,
    create_homework_fixture,
    create_homework_submission_fixture,
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
    homework = await create_homework_fixture(CreateHomeworkFixtureDTO(lesson_student_id=ls.id))

    submission = await create_homework_submission_fixture(
        CreateHomeworkSubmissionFixtureDTO(homework_id=homework.id, status=HomeworkSubmissionStatus.DRAFT)
    )

    res_del = await client_for_tests.delete(
        f"/submissions/{submission.id}?homework_id={homework.id}",
        headers={"Authorization": f"Bearer {t_token}"},
    )
    
    assert res_del.status_code == 200
