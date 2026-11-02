import socket
import tempfile
from pathlib import Path
from types import SimpleNamespace
import pytest
import pytest_asyncio
from passlib.context import CryptContext
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import async_sessionmaker
from src.core.database.database import Base
from tests_unit.integrations_vk.domain.db import require_session as require_f013_session, PORT
from src.modules.db_models import *
from src.modules.integrations_vk.service import IdentityService
from src.modules.users.models import UserRole
from src.modules.users.service import UsersService
from src.modules.users.repository import UsersRepository
from tests_unit.integrations_vk.domain.db import engine, migrate


@pytest.fixture(scope='session', autouse=True)
def network_guard():
    original = socket.socket.connect
    def connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6) and address != ('127.0.0.1', PORT):
            raise AssertionError('F01.3 prohibits external/retained network targets')
        return original(sock, address)
    socket.socket.connect = connect
    yield
    socket.socket.connect = original


@pytest_asyncio.fixture(scope='session')
async def db():
    e = engine()
    with tempfile.TemporaryDirectory(prefix='lgg-domain-media-', dir='/tmp') as root:
        media = Path(root)
        factory = async_sessionmaker(e, expire_on_commit=False, autoflush=False)
        async with factory() as session:
            await require_f013_session(session, e, media, media)
            await session.rollback()
        async with e.begin() as connection:
            await connection.run_sync(migrate)
        yield SimpleNamespace(engine=e, factory=factory, media=media)
    await e.dispose()


@pytest_asyncio.fixture
async def world(db):
    async with db.factory() as session:
        await require_f013_session(session, db.engine, db.media, db.media)
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(delete(table))
        await session.commit()
        crypto = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=4)
        ids = {}
        for key, role, activated in [('t1', UserRole.TEACHER, True), ('t2', UserRole.TEACHER, True),
                                      ('admin', UserRole.ADMIN, True), ('s1', UserRole.STUDENT, True),
                                      ('s2', UserRole.STUDENT, False), ('other', UserRole.STUDENT, True)]:
            user = User(username='synthetic-' + key, hashed_password=crypto.hash('Synthetic-only-123'),
                        role=role, is_active=True, is_activated=activated)
            session.add(user); await session.flush(); ids[key] = user.id
            if role == UserRole.TEACHER:
                session.add(Teacher(user_id=user.id, first_name='Synthetic', last_name=key))
            elif role == UserRole.STUDENT:
                session.add(Student(user_id=user.id, first_name='Synthetic', last_name=key))
        await session.flush()
        t1, t2 = (await session.scalars(__import__('sqlalchemy').select(Teacher).order_by(Teacher.id))).all()
        s1, s2, _ = (await session.scalars(__import__('sqlalchemy').select(Student).order_by(Student.id))).all()
        session.add_all([TeacherStudent(teacher_id=t1.id, student_id=s1.id),
                         TeacherStudent(teacher_id=t1.id, student_id=s2.id)])
        connection = IntegrationConnection(group_id='700', enabled=True)
        second = IntegrationConnection(group_id='701', enabled=True)
        session.add_all([connection, second]); await session.flush()
        session.add_all([ConnectionTeacher(connection_id=c.id, teacher_user_id=ids[t])
                         for c in (connection, second) for t in ('t1','t2')])
        await session.commit()
        def service(s=session):
            users = UsersService.__new__(UsersService)
            users.session_db, users.cr_context, users.users_repo = s, crypto, UsersRepository(s)
            from src.modules.students.repository import StudentRepository
            from src.modules.teachers.repository import TeacherRepository
            users.student_repo, users.teacher_repo = StudentRepository(s), TeacherRepository(s)
            return IdentityService(s, users)
        yield SimpleNamespace(db=db, session=session, ids=ids, connection=connection.id, second=second.id,
            service=service, svc=service(), crypto=crypto, teacher_ids=(t1.id,t2.id), student_ids=(s1.id,s2.id))
