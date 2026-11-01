"""Synthetic-only local preview; never loads dev config. Run after tests finish."""
import asyncio
import json
import os
import secrets
import tempfile
from pathlib import Path
import uvicorn
from passlib.context import CryptContext
from sqlalchemy import select
from src.core.config import create_config
from src.core.config.test_guard import require_test_config
from src.modules.api.app import init_fastapi_app
from src.modules.users.models import User, UserRole
from src.modules.account_invitations.models import AccountInvitation
from src.modules.refresh_tokens.service import token_digest
from src.modules.refresh_tokens.repository import RefreshTokenRepository
from src.modules.account_invitations.repository import InvitationRepository
from datetime import datetime, UTC, timedelta
from zoneinfo import ZoneInfo

root = Path(tempfile.mkdtemp(prefix='lgg-test-media-preview-'))
config = create_config(test=True, media_root=root)
require_test_config(config)
app = init_fastapi_app(config=config)

async def seed() -> None:
    crypto = CryptContext(schemes=['bcrypt'])
    credentials = {}
    users = {}
    run_id = secrets.token_hex(4)
    async with config.db_connection.session_local() as session:
        for role in UserRole:
            name = 't14e_synthetic_' + run_id + '_' + role.value
            user = (await session.execute(select(User).where(User.username == name))).scalar_one_or_none()
            password = secrets.token_urlsafe(18)
            if user is None:
                user = User(username=name, role=role, hashed_password=crypto.hash(password), is_active=True, is_activated=True)
                session.add(user)
            else:
                user.hashed_password = crypto.hash(password)
                user.auth_version += 1
                await RefreshTokenRepository(session).revoke_user(user.id)
            users[role.value] = user
            credentials[role.value] = {'username': name, 'password': password}
        file_password = secrets.token_urlsafe(18)
        file_user = User(username='t14f_synthetic_'+run_id+'_student', role=UserRole.STUDENT, hashed_password=crypto.hash(file_password), is_active=True, is_activated=True)
        session.add(file_user)
        credentials['files_student'] = {'username': file_user.username, 'password': file_password}
        for purpose in ['invite', 'reset']:
            name = 't14e_synthetic_' + run_id + '_' + purpose
            user = (await session.execute(select(User).where(User.username == name))).scalar_one_or_none()
            if user is None:
                user = User(username=name, role=UserRole.STUDENT, hashed_password=crypto.hash(secrets.token_urlsafe(18)), is_active=True, is_activated=purpose == 'reset')
                session.add(user)
            else:
                user.is_activated = purpose == 'reset'
            await session.flush()
            await InvitationRepository(session).invalidate(user.id, purpose)
            raw = secrets.token_urlsafe(48)
            session.add(AccountInvitation(user_id=user.id, purpose=purpose, digest=token_digest(raw), expires_at=datetime.now(UTC)+timedelta(hours=1), consumed=False))
            credentials[purpose] = {'username': name, 'url': 'http://127.0.0.1:5173/' + ('activate' if purpose == 'invite' else 'reset-password') + '#token=' + raw}
        await session.flush()
        # A fresh synthetic file playground; never replace existing records.
        from src.modules.teachers.models import Teacher
        from src.modules.students.models import Student
        from src.modules.teacher_students.models import TeacherStudent
        from src.modules.courses.models import Course, AvatarCoursesType
        from src.modules.student_courses.models import StudentCourse
        from src.modules.lessons.models import Lesson
        from src.modules.lesson_students.models import LessonStudent
        from src.modules.homeworks.models import Homework
        from src.modules.homework_submissions.models import HomeworkSubmission, HomeworkSubmissionStatus
        teacher = Teacher(user_id=users['teacher'].id, first_name='Synthetic', last_name='Teacher')
        student = Student(user_id=file_user.id, first_name='Synthetic', last_name='Student', school_grade=11)
        session.add_all([teacher, student]); await session.flush()
        # Independent synthetic teacher for transport-recovery UI tests (avoid rate-limit coupling).
        recovery_password = secrets.token_urlsafe(18)
        recovery_user = User(username='t15b_recovery_'+run_id, role=UserRole.TEACHER,
            hashed_password=crypto.hash(recovery_password), is_active=True, is_activated=True)
        session.add(recovery_user); await session.flush()
        recovery_teacher = Teacher(user_id=recovery_user.id, first_name='Synthetic', last_name='Recovery')
        session.add(recovery_teacher); await session.flush()
        session.add(TeacherStudent(teacher_id=recovery_teacher.id, student_id=student.id))
        credentials['teacher_recovery'] = {'username': recovery_user.username, 'password': recovery_password}

        session.add(TeacherStudent(teacher_id=teacher.id, student_id=student.id))
        course = Course(teacher_id=teacher.id, name='Synthetic файлы T14f', slug='t14f-'+run_id, avatar_type=AvatarCoursesType.MATHEMATICS)
        session.add(course); await session.flush()
        session.add(StudentCourse(student_id=student.id, course_id=course.id))
        lesson = Lesson(course_id=course.id, teacher_id=teacher.id, title='Synthetic файлы', scheduled_at=datetime.now(ZoneInfo('Europe/Moscow')).replace(hour=15, minute=0, second=0, microsecond=0)+timedelta(days=1))
        session.add(lesson); await session.flush()
        recipient = LessonStudent(lesson_id=lesson.id, student_id=student.id)
        session.add(recipient); await session.flush()
        homework = Homework(lesson_student_id=recipient.id, title='Synthetic файлы T14f')
        session.add(homework); await session.flush()
        from src.modules.homework_placements.models import HomeworkPlacement
        session.add(HomeworkPlacement(homework_id=homework.id, lesson_student_id=recipient.id, kind='original'))
        answer = HomeworkSubmission(homework_id=homework.id, attempt_number=1, version=1, is_working=True, status=HomeworkSubmissionStatus.DRAFT, text_content='Synthetic file playground')
        session.add(answer); await session.flush()
        credentials['files'] = {'homework_id': homework.id, 'submission_id': answer.id}
        from scripts.t15a_seed import seed_read
        await seed_read(session, teacher, student, crypto, run_id, credentials)
        # Planning UI has its own teacher/world; combined E2E must respect login rate limits.
        planning_password = secrets.token_urlsafe(18)
        planning_user = User(username='t15b_planning_'+run_id, role=UserRole.TEACHER,
            hashed_password=crypto.hash(planning_password), is_active=True, is_activated=True)
        session.add(planning_user); await session.flush()
        planning_teacher = Teacher(user_id=planning_user.id, first_name='Synthetic', last_name='Planning')
        session.add(planning_teacher); await session.flush()
        planning_credentials = {}
        await seed_read(session, planning_teacher, student, crypto, run_id + 'planning', planning_credentials)
        credentials['planning_teacher'] = {'username': planning_user.username, 'password': planning_password}
        credentials['planning_student'] = planning_credentials['read_student']
        credentials['planning_read'] = planning_credentials['student_read']
        # Answer mutations have their own student/world so read regressions remain deterministic.
        answer_credentials = {}
        await seed_read(session, teacher, student, crypto, run_id + 'answer', answer_credentials)
        credentials['answer_student'] = answer_credentials['read_student']
        credentials['answer_empty'] = answer_credentials['read_empty']
        credentials['student_answer'] = answer_credentials['student_read']
        profile_credentials = {}
        await seed_read(session, teacher, student, crypto, run_id + 'profile', profile_credentials)
        credentials['profile_student'] = profile_credentials['read_student']
        credentials['password_student'] = profile_credentials['read_empty']
        credentials['student_profile'] = profile_credentials['student_read']
        # Explicit synthetic notification events, including a purged/unavailable target.
        from src.modules.notifications.repository import NotificationsRepository
        profile_id = profile_credentials['student_read']['lessons'][0]['student_user_id']
        homework_id = (await session.execute(select(Homework.id).join(LessonStudent, Homework.lesson_student_id == LessonStudent.id).where(LessonStudent.lesson_id == profile_credentials['student_read']['lessons'][0]['id']))).scalar_one()
        await NotificationsRepository(session).stage(profile_id, 'homework_assigned', 'homework', homework_id, 't15a3-valid-' + run_id)
        await NotificationsRepository(session).stage(profile_id, 'lesson_cancelled', 'lesson', 2147483647, 't15a3-unavailable-' + run_id)
        await session.commit()
    # Seed actual protected assets through the production upload endpoint.
    import httpx
    async with app.router.lifespan_context(app), httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://127.0.0.1:8019') as client:
        response = await client.post('/auth/login', data=credentials['files_student'])
        assert response.status_code == 200, 'Synthetic login failed'
        response = await client.patch(f'/submissions/{answer.id}/student', params={'homework_id': homework.id},
            headers={'Authorization': 'Bearer '+response.json()['access_token']}, data={'expected_version': '1'},
            files=[('files', ('math.pdf', Path('frontend/e2e/fixtures/math.pdf').read_bytes(), 'application/pdf')),
                   ('files', ('notebook.png', Path('frontend/e2e/fixtures/notebook.png').read_bytes(), 'image/png'))])
        assert response.status_code == 200, 'Synthetic file seed failed'
        from scripts.t15a_seed import seed_materials
        await seed_materials(client, credentials)
        await seed_materials(client, {**credentials, "student_read": credentials["student_profile"]})
        from scripts.t15a_seed import archive_seed
        await archive_seed(config, credentials)
        await archive_seed(config, {'student_read': credentials['planning_read']})
        await archive_seed(config, {'student_read': credentials['student_profile']})
        await archive_seed(config, {'student_read': credentials['student_answer']})
    credentials['files']['media_root'] = str(root)
    target = Path('frontend/.artifacts/t14e-credentials.json')
    target.parent.mkdir(exist_ok=True)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, 'w') as out:
        json.dump(credentials, out, indent=2)
    os.chmod(target, 0o600)
    from scripts.preview_login_note import write_login_note
    write_login_note(credentials)
    print('Synthetic credentials saved privately to frontend/.artifacts/t14e-credentials.json')
    await config.db_connection.engine.dispose()

if __name__ == '__main__':
    asyncio.run(seed())
    uvicorn.run(app, host='127.0.0.1', port=8019, access_log=False)
