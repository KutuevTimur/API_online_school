"""Synthetic read fixture extension; called only by guarded preview, after pytest."""
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any
import httpx
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.config.config import Config
from src.modules.students.models import Student
from sqlalchemy import update
from src.modules.users.models import User, UserRole
from src.modules.teachers.models import Teacher
from src.modules.teacher_students.models import TeacherStudent
from src.modules.courses.models import Course, AvatarCoursesType
from src.modules.student_courses.models import StudentCourse
from src.modules.lessons.models import Lesson
from src.modules.lesson_students.models import LessonStudent
from src.modules.homeworks.models import Homework
from src.modules.homework_placements.models import HomeworkPlacement
from src.modules.homework_submissions.models import HomeworkSubmission


async def seed_read(session: AsyncSession, teacher: Teacher, student: Student,
                    crypto: CryptContext, run_id: str, credentials: dict[str, Any]) -> None:
    import secrets
    for purpose in ['read_student', 'read_empty']:
        password = secrets.token_urlsafe(18)
        user = User(username='t15a_'+purpose+'_'+run_id, role=UserRole.STUDENT,
            hashed_password=crypto.hash(password), is_active=True, is_activated=True)
        session.add(user)
        await session.flush()
        credentials[purpose] = {'username':user.username, 'password':password}
        profile = Student(user_id=user.id, first_name='Synthetic', last_name=purpose, school_grade=9 if 'profile' in run_id else 11 if 'answer' in run_id else 10)
        session.add(profile)
        await session.flush()
        if purpose == 'read_student':
            student = profile
    session.add(TeacherStudent(teacher_id=teacher.id, student_id=student.id))
    second = User(username='t15a_teacher_'+run_id, role=UserRole.TEACHER,
        hashed_password=crypto.hash(secrets.token_urlsafe(18)), is_active=True, is_activated=True)
    session.add(second)
    await session.flush()
    other = Teacher(user_id=second.id, first_name='Synthetic', last_name='Second')
    session.add(other)
    await session.flush()
    session.add(TeacherStudent(teacher_id=other.id, student_id=student.id))
    now = datetime.now(UTC)
    fixtures = {'courses': [], 'lessons': []}
    for index, (owner, name, archive) in enumerate([
        (teacher, 'Алгебра · учебный курс', False),
        (other, 'Геометрия · второй преподаватель', False),
        (teacher, 'Архив · повторение', True),
    ]):
        course = Course(teacher_id=owner.id, name=name, slug='t15a-'+run_id+str(index),
            is_deleted=False, avatar_type=AvatarCoursesType.MATHEMATICS, description='Синтетические учебные материалы для проверки кабинета.')
        session.add(course)
        await session.flush()
        session.add(StudentCourse(course_id=course.id, student_id=student.id))
        fixtures['courses'].append(course.id)
        for number, status in enumerate(['scheduled', 'completed', 'cancelled'] if not archive else ['completed']):
            lesson = Lesson(course_id=course.id, teacher_id=owner.id,
                title=['Квадратные уравнения', 'Разбор решения', 'Практика'][number],
                topic='Работа с учебными примерами', scheduled_at=now.astimezone(ZoneInfo('Europe/Moscow')).replace(hour=14+index, minute=0, second=0, microsecond=0)+timedelta(days=number),
                status=status, description='Откройте материалы занятия. Все данные синтетические.')
            session.add(lesson)
            await session.flush()
            recipient = LessonStudent(lesson_id=lesson.id, student_id=student.id)
            session.add(recipient)
            await session.flush()
            homework = Homework(lesson_student_id=recipient.id, title='Задание · '+lesson.title,
                description='Решите уравнение x² − 5x + 6 = 0.')
            session.add(homework)
            await session.flush()
            session.add(HomeworkPlacement(homework_id=homework.id, lesson_student_id=recipient.id, kind='original'))
            if number == 1:
                session.add(HomeworkSubmission(homework_id=homework.id, attempt_number=1,
                    status='checked', is_working=True, grade=0 if index == 0 else 5,
                    checked_at=now-timedelta(hours=index), teacher_comment='Синтетическая проверка.'))
            fixtures['lessons'].append({'id':lesson.id,'course_id':course.id,'teacher_user_id':owner.user_id,
                'student_user_id':student.user_id, 'archive':archive})
    # Hidden foreign course: students must never see it.
    session.add(Course(teacher_id=other.id, name='HIDDEN foreign course', avatar_type=AvatarCoursesType.DEFAULT, slug='hidden-'+run_id))
    credentials['student_read'] = fixtures


async def seed_materials(client: httpx.AsyncClient, credentials: dict[str, Any]) -> None:
    login = await client.post('/auth/login', data=credentials['teacher'])
    assert login.status_code == 200
    token = login.json()['access_token']
    me = (await client.get('/users/me', headers={'Authorization':'Bearer '+token})).json()['id']
    for lesson in credentials['student_read']['lessons']:
        if lesson['teacher_user_id'] != me:
            continue
        response = await client.post('/lectures', headers={'Authorization':'Bearer '+token},
            data={'lesson_id':str(lesson['id']), 'student_user_id':str(lesson['student_user_id'])},
            files={'file':('Учебный пример.pdf',Path('frontend/e2e/fixtures/math.pdf').read_bytes(),'application/pdf')})
        assert response.status_code == 201, 'Synthetic lecture seed failed'


async def archive_seed(config: Config, credentials: dict[str, Any]) -> None:
    async with config.db_connection.session_local() as session:
        for lesson in credentials['student_read']['lessons']:
            if lesson['archive']:
                await session.execute(update(Course).where(Course.id == lesson['course_id']).values(is_deleted=True))
        await session.commit()
