"""T15c.2: seed only an EMPTY guarded disposable database, never the saved preview.
Use a separate volume on the guarded port with the source preview stopped.
Existing private credentials are never overwritten; no reset/delete operations.
"""
import asyncio
import json
import os
import secrets
import tempfile
from pathlib import Path
from passlib.context import CryptContext
from sqlalchemy import text
from src.core.config import create_config
from src.core.config.test_guard import require_test_config
import src.modules.db_models  # noqa: F401
from src.modules.users.models import User, UserRole
from src.modules.teachers.models import Teacher
from src.modules.students.models import Student


async def main():
    os.umask(0o077)
    target = Path('frontend/.artifacts/t15c2-credentials.json')
    assert not target.exists(), 'Do not overwrite existing private credentials'
    root = Path(tempfile.mkdtemp(prefix='lgg-test-media-t15c2-'))
    conf = create_config(test=True, media_root=root)
    require_test_config(conf)
    credentials = {'media_root': str(root)}
    async with conf.db_connection.session_local() as db:
        assert db.bind is conf.db_connection.engine
        assert tuple((await db.execute(text('SELECT current_database(), current_user'))).one()) == ('lgg_test', 'lgg_test_app')
        assert await db.scalar(text('SELECT count(*) FROM users')) == 0, 'Refuse nonempty DB; preserve preview'
        assert await db.scalar(text('SELECT count(*) FROM file_deletions WHERE NOT completed')) == 0
        crypto = CryptContext(schemes=['bcrypt'])
        for key, role in [('admin', UserRole.ADMIN), ('teacher', UserRole.TEACHER), ('other', UserRole.TEACHER), ('student', UserRole.STUDENT)]:
            password = secrets.token_urlsafe(18)
            user = User(username='t15c2_' + secrets.token_hex(6), role=role, hashed_password=crypto.hash(password), is_active=True, is_activated=True)
            db.add(user)
            await db.flush()
            credentials[key] = {'id': user.id, 'username': user.username, 'password': password}
            if role == UserRole.TEACHER:
                db.add(Teacher(user_id=user.id, first_name='Тестовый', last_name='Преподаватель'))
            elif role == UserRole.STUDENT:
                db.add(Student(user_id=user.id, first_name='Тестовый', last_name='Ученик'))
        await db.commit()
    await conf.db_connection.engine.dispose()
    target.write_text(json.dumps(credentials))
    target.chmod(0o600)
    print('PASS four synthetic accounts in empty disposable DB; separate temporary media')


if __name__ == '__main__':
    asyncio.run(main())
