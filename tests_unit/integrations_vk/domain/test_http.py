from contextlib import asynccontextmanager
from types import SimpleNamespace
from uuid import UUID, uuid4
import pytest
from fastapi import Depends
from httpx import AsyncClient, ASGITransport
from src.core.config.config import PathsConfig, TokensConfig
from src.core.config.browser import BrowserConfig
from src.core.database.database import get_db
from src.core.config.synthetic_guard import require_f012_session
from src.modules.api.app import init_fastapi_app
from src.modules.auth.depends import get_current_user
from src.modules.auth.login import oauth2_scheme
from src.modules.users.models_dto import UserDTO
from src.modules.db_models import User
from src.modules.integrations_vk.depends import get_identity_service
from tests_unit.integrations_vk.domain.test_identity import child

pytestmark=pytest.mark.asyncio
HEADERS={'origin':'http://127.0.0.1:5173','x-lgg-request':'browser','content-type':'application/json',
         'authorization':'Bearer synthetic-session','X-LGG-Reauth':'Synthetic-only-123'}


@asynccontextmanager
async def client(w,actor='s1',enabled=True):
    conf=SimpleNamespace(paths=PathsConfig.build(media_root=w.db.media), tokens=TokensConfig(algorithm='HS256'),
        browser=BrowserConfig.build({},'TEST'), file_maintenance_enabled=False,
        env=SimpleNamespace(mode='TEST'), vk_identity_enabled=enabled,
        db_connection=SimpleNamespace(engine=w.db.engine,session_local=w.db.factory))
    app=init_fastapi_app(conf)
    app.state.cr_context=w.crypto
    async def db_override():
        async with w.db.factory() as s:
            await require_f012_session(s,w.db.engine,w.db.media,w.db.media)
            yield s
    async def actor_override(session=Depends(get_db)):
        return UserDTO.model_validate(await session.get(User,w.ids[actor]))
    app.dependency_overrides[get_db]=db_override
    app.dependency_overrides[get_current_user]=actor_override
    # Bearer decoding is an established A03 dependency; identity still reauthenticates
    # against the actual User row/password and binds the exact token/session string.
    async with AsyncClient(transport=ASGITransport(app=app),base_url='http://synthetic') as c:
        yield c


async def test_http_challenge_status_guard_and_real_password(world):
    w=world
    async with client(w) as c:
        body={'operation_id':str(uuid4()),'connection_id':str(w.connection),'purpose':'student'}
        r=await c.post('/users/me/integrations/vk',json=body,headers=HEADERS)
        assert r.status_code==200 and r.headers['cache-control']=='no-store' and r.json()['secret']
        assert (await c.post('/users/me/integrations/vk',json=body,headers=HEADERS)).json()['secret'] is None
        bad=await c.post('/users/me/integrations/vk',json={**body,'vk_id':123},headers=HEADERS)
        assert bad.status_code==422
        assert (await c.post('/users/me/integrations/vk',json=body,headers={**HEADERS,'origin':'https://foreign.invalid'})).status_code==403
        wrong=await c.post('/users/me/integrations/vk',json=body,headers={**HEADERS,'X-LGG-Reauth':'wrong'})
        assert wrong.status_code==401 and wrong.json()['code']=='REAUTH_REQUIRED'
        assert (await c.get('/users/me/integrations/vk',headers=HEADERS)).status_code==200
    async with client(w,enabled=False) as c:
        r=await c.get('/users/me/integrations/vk',headers=HEADERS)
        assert r.status_code==403 and r.json()['code']=='CONNECTION_DISABLED'


async def test_claim_http_fail_closed_and_foreign_direct_ids(world):
    w=world;kid=await child(w)
    async with client(w) as c:
        r=await c.post('/integrations/vk/challenges/claim',json={'operation_id':str(uuid4()),'secret':'x'*43,'actor_context':kid['actor_context']},headers=HEADERS)
        assert r.status_code==401 and r.json()=={'code':'AUTH_REQUIRED','retryable':False}
    async with client(w,'t2') as c:
        r=await c.post('/teacher-planning/recipients/'+kid['recipient_id']+'/resolve-invite',
            json={'operation_id':str(uuid4()),'expected_revision':1,'mode':'new_student'},headers=HEADERS)
        assert r.status_code==404 and r.json()=={'code':'NOT_FOUND','retryable':False}
        r=await c.post('/teacher-planning/parent-grants/'+str(uuid4())+'/confirm',
            json={'operation_id':str(uuid4()),'expected_revision':1},headers=HEADERS)
        assert r.status_code==404


async def test_http_resolve_invite_no_secret_in_replay_or_operation_get(world):
    w=world;kid=await child(w)
    async with client(w,'t1') as c:
        url='/teacher-planning/recipients/'+kid['recipient_id']+'/resolve-invite'
        body={'operation_id':str(uuid4()),'expected_revision':1,'mode':'new_student'}
        first=await c.post(url,json=body,headers=HEADERS)
        assert first.status_code==200 and first.json()['invitation']['activation_link']
        replay=await c.post(url,json=body,headers=HEADERS)
        assert replay.status_code==200 and replay.json()['invitation'] is None
        op=await c.get('/users/me/integrations/vk/operations/'+body['operation_id'],params={'action':'recipient_resolve'},headers=HEADERS)
        assert op.status_code==200 and op.json()['result']['invitation_issued'] and 'activation_link' not in op.text
    async with client(w,'t2') as c:
        op=await c.get('/users/me/integrations/vk/operations/'+body['operation_id'],params={'action':'recipient_resolve'},headers=HEADERS)
        assert op.status_code==404
