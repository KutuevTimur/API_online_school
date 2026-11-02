from uuid import UUID
import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import delete, text
from sqlalchemy.exc import IntegrityError
from src.core.database.database import Base
from tests_unit.integrations_vk.domain.db import require_connection as require_f013_connection, require_session as require_f013_session
from src.core.config.synthetic_guard import require_f013_url
from src.modules.db_models import *
from tests_unit.integrations_vk.domain.db import migrate, downgrade
from tests_unit.integrations_vk.domain.test_identity import child, linked

pytestmark = pytest.mark.asyncio


async def test_clean_prior_schema_preservation_and_safe_downgrade(db):
    async with db.factory() as s:
        await require_f013_session(s,db.engine,db.media,db.media)
        for table in reversed(Base.metadata.sorted_tables):await s.execute(delete(table))
        await s.commit()
    async with db.engine.begin() as c:
        await c.run_sync(lambda conn:downgrade(conn,'base'))
        await c.run_sync(migrate)
        def compare(conn):
            require_f013_connection(conn)
            return compare_metadata(MigrationContext.configure(conn,opts={'compare_server_default':True}),Base.metadata)
        assert await c.run_sync(compare)==[]
        await c.run_sync(lambda conn:downgrade(conn,'e738d7c0dec3'))
        await c.execute(text("INSERT INTO users(username,role,hashed_password,is_active) VALUES('synthetic_prior_f012','student','synthetic',true)"))
        prior=(await c.execute(text('SELECT id, username, hashed_password FROM users'))).all()
        await c.run_sync(migrate)
        assert (await c.execute(text('SELECT id, username, hashed_password FROM users'))).all()==prior
        assert await c.run_sync(compare)==[]
        await c.execute(text("INSERT INTO vk_connections(id,installation_id,group_id,enabled) VALUES('00000000-0000-0000-0000-000000000001','00000000-0000-0000-0000-000000000002','synthetic',false)"))
    with pytest.raises(RuntimeError,match='Refusing to discard VK identity'):
        async with db.engine.begin() as c:await c.run_sync(lambda conn:downgrade(conn,'e738d7c0dec3'))
    async with db.engine.connect() as c:
        assert (await c.execute(text('SELECT version_num FROM alembic_version'))).scalar_one()=='f01320261102'
        assert (await c.execute(text('SELECT count(*) FROM vk_connections'))).scalar_one()==1


@pytest.mark.parametrize('case', ['contact_scope','recipient_revision','recipient_grade','identity_scope','recipient_user_unique','identity_contact_unique','identity_user_unique','grant_state','grant_proof','grant_scope','challenge_digest','operation_shape'])
async def test_constraints_reject_invalid_state(world,case):
    w=world;c,ch=await linked(w);rid=c['recipient_id']
    context=(await w.session.execute(text('SELECT contact_id FROM vk_actor_contexts LIMIT 1'))).scalar_one()
    params={'c':w.connection,'other':w.second,'r':UUID(rid),'contact':context,'user':w.ids['s1'],'actor':w.ids['t1']}
    sql={
      'contact_scope':"INSERT INTO vk_recipients(id,connection_id,child_contact_id,first_name,last_name,revision) VALUES(gen_random_uuid(),:other,:contact,'X','Y',1)",
      'recipient_revision':"UPDATE vk_recipients SET revision=0 WHERE id=:r",
      'recipient_grade':"UPDATE vk_recipients SET grade=12 WHERE id=:r",
      'identity_scope':"UPDATE vk_identity_links SET connection_id=:other WHERE contact_id=:contact",
      'recipient_user_unique':"INSERT INTO vk_recipients(id,connection_id,child_contact_id,first_name,last_name,linked_student_user_id,revision) SELECT gen_random_uuid(),:c,id,'X','Y',:user,1 FROM vk_contacts WHERE subject='102'",
      'identity_contact_unique':"INSERT INTO vk_identity_links(id,connection_id,contact_id,user_id,purpose,verified_method,verified_by,revision) VALUES(gen_random_uuid(),:c,:contact,:actor,'student','synthetic',:actor,1)",
      'identity_user_unique':"INSERT INTO vk_identity_links(id,connection_id,contact_id,user_id,purpose,verified_method,verified_by,revision) SELECT gen_random_uuid(),:c,id,:user,'student','synthetic',:actor,1 FROM vk_contacts WHERE subject='102'",
      'grant_state':"INSERT INTO vk_parent_grants(id,connection_id,parent_contact_id,recipient_id,teacher_user_id,state,revision) VALUES(gen_random_uuid(),:c,:contact,:r,:actor,'unknown',1)",
      'grant_proof':"INSERT INTO vk_parent_grants(id,connection_id,parent_contact_id,recipient_id,teacher_user_id,state,revision) VALUES(gen_random_uuid(),:c,:contact,:r,:actor,'confirmed',1)",
      'grant_scope':"INSERT INTO vk_parent_grants(id,connection_id,parent_contact_id,recipient_id,teacher_user_id,state,revision) VALUES(gen_random_uuid(),:other,:contact,:r,:actor,'pending',1)",
      'challenge_digest':"INSERT INTO vk_identity_challenges SELECT gen_random_uuid(), connection_id, revision, user_id, purpose, digest, session_digest, auth_version, expected_link_revision, claimed_contact_id, expires_at, consumed_at FROM vk_identity_challenges LIMIT 1",
      'operation_shape':"UPDATE vk_identity_operations SET result=NULL WHERE state='committed'",
    }[case]
    if case in {'recipient_user_unique','identity_user_unique'}:await child(w,'102')
    if case=='challenge_digest':
        # Explicit columns avoid dependence on ORM/table field order.
        sql="INSERT INTO vk_identity_challenges(id,connection_id,revision,user_id,purpose,digest,session_digest,auth_version,expected_link_revision,claimed_contact_id,expires_at,consumed_at) SELECT gen_random_uuid(),connection_id,revision,user_id,purpose,digest,session_digest,auth_version,expected_link_revision,claimed_contact_id,expires_at,consumed_at FROM vk_identity_challenges LIMIT 1"
    with pytest.raises(IntegrityError):
        async with w.session.begin_nested():await w.session.execute(text(sql),params)


@pytest.mark.parametrize('url', [
    'postgresql+asyncpg://lgg_test_app:x@127.0.0.1:55432/lgg_test',
    'postgresql+asyncpg://lgg_f012_app:x@127.0.0.1:55431/lgg_f012',
    'postgresql+asyncpg://postgres:x@127.0.0.1:55434/lgg_f013',
    'postgresql+asyncpg://lgg_f013_app:x@remote:55434/lgg_f013',
    'postgresql+asyncpg://lgg_f013_app:x@127.0.0.1:55434/lgg_f013?options=unsafe',
    'postgresql+asyncpg://lgg_f012_app:x@127.0.0.1:55433/lgg_f012',
])
async def test_guard_refuses_retained_or_unknown_before_connect(url):
    with pytest.raises(RuntimeError):require_f013_url(url)


async def test_session_and_media_guard_refuses_mismatch_before_sql(db):
    from types import SimpleNamespace
    with pytest.raises(RuntimeError):await require_f013_session(SimpleNamespace(bind=None),db.engine,db.media,db.media)
    async with db.factory() as s:
        with pytest.raises(RuntimeError):await require_f013_session(s,db.engine,db.media,db.media/'other')
