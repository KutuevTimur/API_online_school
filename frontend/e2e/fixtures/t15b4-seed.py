"""Synthetic browser fixture; refuses nonempty DB, uses its own temporary media.
Run only on the isolated guarded disposable volume after the backend suite.
"""
import asyncio
import json
import os
import secrets
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from passlib.context import CryptContext
from sqlalchemy import select, func, text
from src.core.config import create_config
from src.core.config.test_guard import require_test_config
import src.modules.db_models  # noqa: F401
from src.modules.users.models import User, UserRole
from src.modules.teachers.models import Teacher
from src.modules.students.models import Student
from src.modules.teacher_students.models import TeacherStudent
from src.modules.courses.models import Course, AvatarCoursesType
from src.modules.student_courses.models import StudentCourse
from src.modules.lessons.models import Lesson
from src.modules.lesson_students.models import LessonStudent


async def main():
    os.umask(0o077)
    root=Path(tempfile.mkdtemp(prefix='lgg-test-media-t15b4-'))
    conf=create_config(test=True,media_root=root);require_test_config(conf)
    credentials={'media_root':str(root)}
    crypto=CryptContext(schemes=['bcrypt'])
    async with conf.db_connection.session_local() as db:
        assert tuple((await db.execute(text('SELECT current_database(),current_user'))).one())==('lgg_test','lgg_test_app')
        assert await db.scalar(select(func.count()).select_from(User))==0, 'Refuse to seed a nonempty database; preserve preview'
        users={}
        for key,role in [('teacher',UserRole.TEACHER),('student',UserRole.STUDENT),('other',UserRole.TEACHER)]:
            password=secrets.token_urlsafe(18)
            user=User(username=f't15b4_{secrets.token_hex(4)}',role=role,hashed_password=crypto.hash(password),is_active=True)
            db.add(user);await db.flush();users[key]=user
            credentials[key]={'id':user.id,'username':user.username,'password':password}
        teacher=Teacher(user_id=users['teacher'].id,first_name='Тестовый',last_name='Учитель')
        other=Teacher(user_id=users['other'].id,first_name='Другой',last_name='Учитель')
        student=Student(user_id=users['student'].id,first_name='Тестовый',last_name='Ученик',school_grade=10)
        db.add_all([teacher,other,student]);await db.flush()
        db.add_all([TeacherStudent(teacher_id=t.id,student_id=student.id,lesson_price_kopecks=80025 if t==teacher else 90000) for t in [teacher,other]])
        course=Course(teacher_id=teacher.id,name='Тестовый Ученик',slug='t15b4-synthetic',avatar_type=AvatarCoursesType.MATHEMATICS)
        db.add(course);await db.flush()
        now=datetime.now(ZoneInfo('Europe/Moscow'));start=now.replace(hour=0,minute=0,second=0,microsecond=0)-timedelta(days=now.weekday())
        db.add(StudentCourse(course_id=course.id,student_id=student.id,started_at=start-timedelta(days=14)))
        cases=[(start+timedelta(hours=12),'completed',80025,False),
               (start+timedelta(hours=14),'completed',None,False),
               (start+timedelta(days=6,hours=20),'scheduled',80025,False),
               (start+timedelta(days=1,hours=15),'cancelled',90000,False),
               (start-timedelta(days=7)+timedelta(hours=12),'completed',100010,False),
               (start+timedelta(hours=16),'completed',99900,True)]
        for index,(at,status,price,archived) in enumerate(cases):
            lesson=Lesson(course_id=course.id,teacher_id=teacher.id,title=f'Тест цены {index}',scheduled_at=at,status=status,lesson_price_kopecks=price,is_deleted=archived,deleted_at=now if archived else None)
            db.add(lesson);await db.flush();db.add(LessonStudent(lesson_id=lesson.id,student_id=student.id))
        await db.commit()
        credentials.update(week=start.date().isoformat(),previous_week=(start-timedelta(days=7)).date().isoformat())
    await conf.db_connection.engine.dispose()
    target=Path('frontend/.artifacts/t15b4-credentials.json');target.write_text(json.dumps(credentials));target.chmod(0o600)
    print('PASS isolated browser fixture; dedicated temporary media; no preview accounts used')


if __name__=='__main__':asyncio.run(main())
