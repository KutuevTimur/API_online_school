"""Fresh F01.4 synthetic preview only. No env files, retained engines, external I/O.

Run seed once after DB tests, then serve. Does not reset an existing database.
"""
import asyncio
import json
import secrets
import socket
import sys
import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

from alembic import command
from alembic.config import Config as AlembicConfig
from passlib.context import CryptContext
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.core.config.config import PathsConfig, TokensConfig, AllowedExtensions
from src.core.config.browser import BrowserConfig
from src.core.config.synthetic_guard import F014_URL, require_f014_url, require_f014_session, require_f014_connection
from src.core.database.database import get_db
from src.modules.api.app import init_fastapi_app
from src.modules.db_models import *
from src.modules.users.models import UserRole
from src.modules.integrations_vk.service import IdentityService
from src.modules.integrations_vk.booking_service import BookingService
from src.modules.integrations_vk.models_dto import Candidate, PublishWindowsRequest, WindowItem, PrepareBookingRequest, ConfirmBookingRequest
from src.modules.users.service import UsersService
from src.modules.users.repository import UsersRepository
from src.modules.students.repository import StudentRepository
from src.modules.teachers.repository import TeacherRepository

NOTE = Path('frontend/.artifacts/f014-preview.json')
_connect = socket.socket.connect

def connect(sock, address):
    if sock.family in (socket.AF_INET, socket.AF_INET6) and address != ('127.0.0.1', 55435):
        raise RuntimeError('F01.4 prohibits external/retained network targets')
    return _connect(sock, address)

socket.socket.connect = connect
require_f014_url(F014_URL)
engine = create_async_engine(F014_URL)
factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
crypto = CryptContext(schemes=['bcrypt'], deprecated='auto', bcrypt__rounds=4)

def identity(session):
    users = UsersService.__new__(UsersService)
    users.session_db, users.cr_context = session, crypto
    users.users_repo, users.student_repo, users.teacher_repo = UsersRepository(session), StudentRepository(session), TeacherRepository(session)
    return IdentityService(session, users)

async def seed():
    if NOTE.exists():
        raise RuntimeError('Preview already allocated; refusing seed/reset')
    media = Path(tempfile.mkdtemp(prefix='lgg-f014-preview-', dir='/tmp'))
    async with factory() as s:
        await require_f014_session(s, engine, media, media)
        if await s.scalar(select(func.count()).select_from(User)):
            # Test suite leaves data: seed is additive, never a reset.
            pass
        await s.rollback()
        accounts = {}
        ids = {}
        for key, role in [('teacher',UserRole.TEACHER),('teacher2',UserRole.TEACHER),('student',UserRole.STUDENT)]:
            password = secrets.token_urlsafe(18)
            user = User(username='f014_' + key + '_' + secrets.token_hex(3), role=role,
                        hashed_password=crypto.hash(password), is_active=True, is_activated=True)
            s.add(user); await s.flush(); ids[key] = user.id
            accounts[key] = {'username':user.username,'password':password}
            profile = Teacher(user_id=user.id,first_name='Synthetic',last_name=key) if role==UserRole.TEACHER else Student(user_id=user.id,first_name='Synthetic',last_name='Существующий',school_grade=8)
            s.add(profile)
        await s.flush()
        teacher = await s.scalar(select(Teacher).where(Teacher.user_id==ids['teacher']))
        student = await s.scalar(select(Student).where(Student.user_id==ids['student']))
        s.add(TeacherStudent(teacher_id=teacher.id,student_id=student.id))
        connection = IntegrationConnection(group_id='f014-'+secrets.token_hex(3), enabled=True)
        s.add(connection); await s.flush()
        s.add_all([ConnectionTeacher(connection_id=connection.id,teacher_user_id=ids[k]) for k in ('teacher','teacher2')])
        await s.commit()
        svc=identity(s); bookings=BookingService(s,svc.users)
        # Stable future acceptance week, independent of wall clock at next opening.
        start=datetime(2030,1,7,12,tzinfo=UTC)
        refs=[]
        for index, name in enumerate(['Приёмка','Автопроверка','Существующий']):
            kid=await svc.observe_trusted(connection.id,connection.group_id,str(1000+index),str(1000+index),ids['teacher'],Candidate(first_name=name,last_name='Synthetic',grade=8))
            if index in (0, 1):
                await svc.observe_trusted(connection.id,connection.group_id,'2000','2000',ids['teacher'],Candidate(first_name='Ignored',last_name='Parent'),child_subject=str(1000+index))
            at=start+timedelta(hours=index)
            published=await bookings.publish(ids['teacher'],PublishWindowsRequest(operation_id=uuid4(),connection_id=connection.id,week_start=start.date(),items=[WindowItem(start_at=at,end_at=at+timedelta(minutes=55))]))
            prepared=await bookings.prepare(PrepareBookingRequest(actor_context=kid['actor_context'],recipient_id=UUID(kid['recipient_id']),window_id=UUID(published.result['window_ids'][0]),expected_revision=1))
            op=await bookings.confirm_booking(ConfirmBookingRequest(operation_id=prepared['operation_id'],actor_context=kid['actor_context'],handle=prepared['handle'],expected_revision=1))
            refs.append({'name':name,'booking_id':op.result['booking_id'],'actor_context':kid['actor_context']})
        NOTE.parent.mkdir(exist_ok=True)
        NOTE.write_text(json.dumps({'media':str(media),'secret':secrets.token_urlsafe(48),'accounts':accounts,'ids':ids,'connection':str(connection.id),'bookings':refs},ensure_ascii=False))
        NOTE.chmod(0o600)
    await engine.dispose()
    print('F01.4 additive fixture allocated; local credentials in ignored note.')

async def preflight(media):
    async with factory() as session:
        await require_f014_session(session,engine,media,media)
    await engine.dispose()


def serve():
    import uvicorn
    note=json.loads(NOTE.read_text()); media=Path(note['media'])
    asyncio.run(preflight(media))
    config=SimpleNamespace(paths=PathsConfig.build(media_root=media), tokens=TokensConfig(algorithm='HS256'),
        browser=BrowserConfig.build({'BROWSER_ORIGIN':'http://127.0.0.1:5174'},'TEST').model_copy(update={'cookie_name':'lgg_f014_refresh'}),
        file_maintenance_enabled=False,vk_identity_enabled=True,allowed_extensions=AllowedExtensions.build(),
        photo_originals_approved=False,legacy_file_reads=True,
        env=SimpleNamespace(mode='TEST',secret_key=note['secret']),
        db_connection=SimpleNamespace(engine=engine,session_local=factory))
    app=init_fastapi_app(config)
    async def guarded_db():
        async with factory() as session:
            await require_f014_session(session,engine,media,media)
            yield session
    app.dependency_overrides[get_db]=guarded_db
    uvicorn.run(app,host='127.0.0.1',port=8020,access_log=False)

async def prepare_flow():
    note=json.loads(NOTE.read_text()); media=Path(note['media'])
    async with factory() as s:
        await require_f014_session(s,engine,media,media)
        connection=await s.get(IntegrationConnection,UUID(note['connection']))
        svc=identity(s); bookings=BookingService(s,svc.users)
        subject=str(300000+secrets.randbelow(100000))
        kid=await svc.observe_trusted(connection.id,connection.group_id,subject,subject,note['ids']['teacher'],Candidate(first_name='Автопроверка2',last_name='Synthetic',grade=8))
        await svc.observe_trusted(connection.id,connection.group_id,'2000','2000',note['ids']['teacher'],Candidate(first_name='Ignored',last_name='Parent'),child_subject=subject)
        at=datetime(2030,1,8,13,tzinfo=UTC)
        published=await bookings.publish(note['ids']['teacher'],PublishWindowsRequest(operation_id=uuid4(),connection_id=connection.id,week_start=datetime(2030,1,7).date(),items=[WindowItem(start_at=at,end_at=at+timedelta(minutes=55))]))
        prepared=await bookings.prepare(PrepareBookingRequest(actor_context=kid['actor_context'],recipient_id=UUID(kid['recipient_id']),window_id=UUID(published.result['window_ids'][0]),expected_revision=1))
        op=await bookings.confirm_booking(ConfirmBookingRequest(operation_id=prepared['operation_id'],actor_context=kid['actor_context'],handle=prepared['handle'],expected_revision=1))
        note['bookings'][1]={'name':'Автопроверка2','booking_id':op.result['booking_id'],'actor_context':kid['actor_context']}
        NOTE.write_text(json.dumps(note,ensure_ascii=False))
    await engine.dispose()
    print('Fresh additive automated flow fixture ready; manual booking preserved')

async def prepare_e2e():
    note=json.loads(NOTE.read_text()); media=Path(note['media'])
    async with factory() as s:
        await require_f014_session(s,engine,media,media)
        connection=await s.get(IntegrationConnection,UUID(note['connection']))
        await identity(s).observe_trusted(connection.id,connection.group_id,'2000','2000',note['ids']['teacher'],Candidate(first_name='Ignored',last_name='Parent'),child_subject='1001')
    await engine.dispose()
    print('Synthetic parent fixture ready')

async def claim():
    from src.modules.integrations_vk.models_dto import ClaimChallengeRequest
    note=json.loads(NOTE.read_text()); media=Path(note['media'])
    data=json.loads(sys.stdin.read())
    async with factory() as s:
        await require_f014_session(s,engine,media,media)
        svc=identity(s)
        connection=await s.get(IntegrationConnection,UUID(note['connection']))
        context=await svc.observe_trusted(connection.id,connection.group_id,'1002','1002',note['ids']['teacher'],Candidate(first_name='Существующий',last_name='Synthetic'))
        await svc.claim_challenge(ClaimChallengeRequest(operation_id=uuid4(),actor_context=context['actor_context'],secret=data['secret']))
    await engine.dispose()
    print('Synthetic claim PASS')

if __name__=='__main__':
    if sys.argv[1:] == ['seed']: asyncio.run(seed())
    elif sys.argv[1:] == ['serve']: serve()
    elif sys.argv[1:] == ['claim']: asyncio.run(claim())
    elif sys.argv[1:] == ['prepare-e2e']: asyncio.run(prepare_e2e())
    elif sys.argv[1:] == ['prepare-flow']: asyncio.run(prepare_flow())
    else: raise SystemExit('Use seed or serve; target fixed at F01.4 DB55435')
