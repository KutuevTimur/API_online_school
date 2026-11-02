"""F01.4 own reads, capability rollback and real activation across roles."""
from uuid import UUID, uuid4
import pytest
from src.modules.db_models import *
from src.modules.integrations_vk.models_dto import Candidate
from tests_unit.integrations_vk.domain.test_http import client, HEADERS
from tests_unit.integrations_vk.domain.test_identity import child
from tests_unit.integrations_vk.domain.test_booking import book

pytestmark = pytest.mark.asyncio


async def test_ui_read_scope_revision_parent_and_disabled_reads(world):
    w = world
    kid = await child(w)
    await w.svc.observe_trusted(w.connection, '700', '202', '202', w.ids['t1'],
        Candidate(first_name='Ignored', last_name='Parent'), child_subject='101')
    booking = await book(w, kid)
    bid = booking.result['booking_id']
    async with client(w, 't1') as c:
        caps = await c.get('/teacher-planning/booking-capabilities', headers=HEADERS)
        assert caps.status_code == 200 and len(caps.json()['items']) == 2
        r = await c.get('/teacher-planning/bookings/' + bid, headers=HEADERS)
        assert r.status_code == 200
        recipient = r.json()['recipient']
        assert recipient['revision'] == 1 and recipient['linked_student_user_id'] is None
        assert len(recipient['parent_grants']) == 1 and recipient['parent_grants'][0]['state'] == 'pending'
        assert recipient['parent_grants'][0]['parent_label'] == 'Родитель · …02'
        assert 'subject' not in r.text and 'actor_context' not in r.text
        calendar = await c.get('/teacher-planning/booking-calendar?week_start=2030-01-07', headers=HEADERS)
        assert calendar.status_code == 200 and calendar.json()['items'][0]['booking_id'] == bid
    async with client(w, 't2') as c:
        assert (await c.get('/teacher-planning/bookings/' + bid, headers=HEADERS)).status_code == 404
        calendar = await c.get('/teacher-planning/booking-calendar?week_start=2030-01-07', headers=HEADERS)
        assert calendar.json()['items'] == []
    async with client(w, 's1') as c:
        assert (await c.get('/teacher-planning/booking-capabilities', headers=HEADERS)).status_code == 403
        assert (await c.get('/teacher-planning/booking-calendar?week_start=2030-01-07', headers=HEADERS)).status_code == 403
    async with client(w, 't1', enabled=False) as c:
        assert (await c.get('/teacher-planning/booking-capabilities', headers=HEADERS)).json()['enabled'] is False
        assert (await c.get('/teacher-planning/bookings/' + bid, headers=HEADERS)).status_code == 200
        assert (await c.post('/teacher-planning/bookings/' + bid + '/materialize', json={'operation_id':str(uuid4()),'expected_revision':1,'expected_recipient_revision':1}, headers=HEADERS)).status_code == 403
    connection = await w.session.get(IntegrationConnection, w.connection)
    connection.enabled = False
    await w.session.commit()
    async with client(w, 't1') as c:
        assert (await c.get('/teacher-planning/bookings/' + bid, headers=HEADERS)).status_code == 200


async def test_ui_resolve_receipt_and_real_invitation_consume(world):
    w = world; kid = await child(w); booking = await book(w, kid)
    bid = booking.result['booking_id']; operation = str(uuid4())
    async with client(w, 't1') as c:
        r = await c.post('/teacher-planning/bookings/' + bid + '/resolve-invite', headers=HEADERS,
            json={'operation_id':operation,'expected_revision':1,'expected_recipient_revision':1,'mode':'new_student'})
        assert r.status_code == 200
        invitation = r.json()['invitation']
        assert invitation and invitation['activation_link']
        assert r.json()['student_username']
        row = (await c.get('/teacher-planning/bookings/' + bid, headers=HEADERS)).json()
        assert row['booking_id'] == bid and row['lesson_id'] and row['access_state'] == 'inactive'
        linked = await c.get('/teacher-planning/linked-bookings', params={'connection_id':str(w.connection),'student_user_id':row['recipient']['linked_student_user_id']},headers=HEADERS)
        assert linked.status_code == 200 and linked.json()['items'][0]['booking_id'] == bid
        op = await c.get('/users/me/integrations/vk/operations/' + operation + '?action=recipient_resolve', headers=HEADERS)
        assert op.status_code == 200 and 'activation_link' not in op.text
        from urllib.parse import urlsplit, parse_qs
        token = parse_qs(urlsplit(invitation['activation_link']).fragment)['token'][0]
        consume = await c.post('/account_invitations/consume', json={'token':token,'purpose':'invite','new_password':'Synthetic-active-123'})
        assert consume.status_code == 200
        assert (await c.get('/teacher-planning/bookings/' + bid, headers=HEADERS)).json()['access_state'] == 'active'


async def test_preview_cookie_isolation_does_not_replace_retained_cookie(world):
    async with client(world, 't1', cookie_name='lgg_f014_refresh') as c:
        c.cookies.set('lgg_refresh', 'retained-placeholder', domain='synthetic.local', path='/auth/browser')
        headers={**HEADERS,'content-type':'application/x-www-form-urlencoded'}
        login=await c.post('/auth/browser/login', data={'username':'synthetic-t1','password':'Synthetic-only-123'},headers=headers)
        assert login.status_code == 200
        assert 'lgg_f014_refresh=' in login.headers['set-cookie']
        assert ' lgg_refresh=' not in login.headers['set-cookie']
        # Browser cookie has /api path; ASGI route has no proxy prefix.
        raw=login.cookies['lgg_f014_refresh']
        refresh=await c.post('/auth/browser/refresh',headers=HEADERS,cookies={'lgg_f014_refresh':raw,'lgg_refresh':'retained-placeholder'})
        assert refresh.status_code == 200
        logout=await c.post('/auth/browser/logout',headers=HEADERS,cookies={'lgg_f014_refresh':refresh.cookies['lgg_f014_refresh'],'lgg_refresh':'retained-placeholder'})
        assert logout.status_code == 200 and 'lgg_f014_refresh=' in logout.headers['set-cookie']
        assert ' lgg_refresh=' not in logout.headers['set-cookie']


async def test_default_browser_cookie_contract_is_preserved(world):
    async with client(world, 't1') as c:
        headers={**HEADERS,'content-type':'application/x-www-form-urlencoded'}
        login=await c.post('/auth/browser/login',data={'username':'synthetic-t1','password':'Synthetic-only-123'},headers=headers)
        assert login.status_code == 200 and login.headers['set-cookie'].startswith('lgg_refresh=')
        c.cookies.set('lgg_refresh',login.cookies['lgg_refresh'])
        refresh=await c.post('/auth/browser/refresh',headers=HEADERS)
        assert refresh.status_code == 200 and refresh.headers['set-cookie'].startswith('lgg_refresh=')
