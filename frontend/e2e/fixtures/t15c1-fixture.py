"""Add an isolated synthetic namespace without reset; verify original rows/media/login files.
Never runs pytest fixtures, consumes owner invitations, or rewrites preview helpers.
"""
import asyncio
import hashlib
import json
import os
import secrets
import sys
from pathlib import Path
from passlib.context import CryptContext
from sqlalchemy import text
from src.core.config import create_config
from src.core.config.test_guard import require_test_config
import src.modules.db_models  # noqa: F401
from src.modules.users.models import User, UserRole
from src.modules.teachers.models import Teacher
from src.modules.students.models import Student

ART = Path('frontend/.artifacts')
TARGET = ART / 't15c1-credentials.json'
SNAPSHOT = ART / 't15c1-preservation.json'
TABLES = ('users', 'teachers', 'students', 'teacher_students', 'courses', 'student_courses',
          'lessons', 'lesson_students', 'homeworks', 'homework_submissions', 'file_assets')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

async def main():
    os.umask(0o077)
    owner = json.loads((ART / 't14e-credentials.json').read_text())
    root = Path(owner['files']['media_root']).resolve()
    assert root.is_dir() and root.name.startswith('lgg-test-media-preview-')
    conf = create_config(test=True, media_root=root)
    require_test_config(conf)
    files = [p for p in root.rglob('*') if p.is_file()] + [ART / 't14e-credentials.json', ART / 't15b1-login.txt', ART / 't15b2-resume.py']
    async with conf.db_connection.session_local() as db:
        assert db.bind is conf.db_connection.engine
        assert tuple((await db.execute(text('SELECT current_database(), current_user'))).one()) == ('lgg_test', 'lgg_test_app')
        if '--verify' in sys.argv:
            snap = json.loads(SNAPSHOT.read_text())
            for table, rows in snap['rows'].items():
                actual = {str(row[0]): hashlib.sha256(row[1].encode()).hexdigest() for row in await db.execute(text(f'SELECT id, row_to_json(t)::text FROM {table} t'))}
                assert all(actual.get(key) == value for key, value in rows.items()), table
            assert all(Path(p).is_file() and digest(Path(p)) == value for p, value in snap['files'].items())
            print('PASS original rows, media checksums and exact preview credentials/helpers preserved')
        else:
            assert not TARGET.exists() and not SNAPSHOT.exists(), 'Fixture already allocated; do not overwrite'
            snap = {'rows': {}, 'files': {str(p): digest(p) for p in files}}
            for table in TABLES:
                snap['rows'][table] = {str(row[0]): hashlib.sha256(row[1].encode()).hexdigest() for row in await db.execute(text(f'SELECT id, row_to_json(t)::text FROM {table} t'))}
            credentials = {}
            crypto = CryptContext(schemes=['bcrypt'])
            for key, role in [('admin', UserRole.ADMIN), ('teacher', UserRole.TEACHER), ('other', UserRole.TEACHER), ('student', UserRole.STUDENT)]:
                password = secrets.token_urlsafe(18)
                user = User(username='t15c1_' + secrets.token_hex(6), role=role, hashed_password=crypto.hash(password), is_active=True, is_activated=True)
                db.add(user)
                await db.flush()
                credentials[key] = {'id': user.id, 'username': user.username, 'password': password}
                if role == UserRole.TEACHER:
                    db.add(Teacher(user_id=user.id, first_name='Тестовый', last_name='Преподаватель'))
                if role == UserRole.STUDENT:
                    db.add(Student(user_id=user.id, first_name='Тестовый', last_name='Ученик'))
            await db.commit()
            TARGET.write_text(json.dumps(credentials)); TARGET.chmod(0o600)
            SNAPSHOT.write_text(json.dumps(snap)); SNAPSHOT.chmod(0o600)
            print('PASS additive namespace: four new synthetic accounts; original preview untouched')
    await conf.db_connection.engine.dispose()

if __name__ == '__main__':
    asyncio.run(main())
