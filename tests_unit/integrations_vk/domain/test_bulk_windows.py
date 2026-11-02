from datetime import timedelta
from uuid import uuid4
import asyncio
import pytest
from src.modules.db_models import BookingWindow, Booking, IdentityOperation
from src.modules.integrations_vk.models_dto import CloseWindowsRequest, CloseWindowItem
from src.modules.integrations_vk.exception import IdentityError
from tests_unit.integrations_vk.domain.test_booking import svc, window, START, prepared, confirm
from tests_unit.integrations_vk.domain.test_identity import child, rev, count
from tests_unit.integrations_vk.domain.test_http import client, HEADERS

pytestmark=pytest.mark.asyncio

def batch(w, ids, revisions=None):
    return CloseWindowsRequest(operation_id=uuid4(),connection_id=w.connection,
        items=[CloseWindowItem(window_id=id,expected_revision=(revisions or {}).get(id,1)) for id in ids])

async def test_bulk_close_atomic_receipt_replay_and_payload(world):
    w=world;a=await window(w);b=await window(w,START+timedelta(hours=1));data=batch(w,[a,b])
    first=await svc(w).close_windows(w.ids['t1'],data)
    assert first.result['kind']=='windows_closed' and set(first.result['window_ids'])=={str(a),str(b)}
    assert (await svc(w).close_windows(w.ids['t1'],data)).result==first.result
    for id in (a,b):
        row=await w.session.get(BookingWindow,id)
        assert row.status=='closed' and row.withdrawn and row.revision==2
    with pytest.raises(IdentityError,match='PAYLOAD_MISMATCH'):
        await svc(w).close_windows(w.ids['t1'],data.model_copy(update={'items':data.items[:1]}))
    assert len((await svc(w).list_windows(w.ids['t1'],w.connection,START.date())).items)==2
    assert (await svc(w).list_windows(w.ids['t1'],w.connection,START.date(),published_only=True)).items==[]
    op=await w.svc.operation_status(w.ids['t1'],data.operation_id,'windows_close')
    assert op.result==first.result

async def test_bulk_stale_rolls_back_entire_batch(world):
    w=world;a=await window(w);b=await window(w,START+timedelta(hours=1));await svc(w).close(w.ids['t1'],b,rev())
    with pytest.raises(IdentityError,match='STALE_REVISION'):await svc(w).close_windows(w.ids['t1'],batch(w,[a,b]))
    row=await w.session.get(BookingWindow,a);assert row.status=='published' and row.revision==1

async def test_bulk_consumed_keeps_booking_and_other_window(world):
    w=world;a=await window(w);b=await window(w,START+timedelta(hours=1));kid=await child(w)
    handle=await prepared(w,kid,b);await svc(w).confirm_booking(confirm(kid,handle))
    with pytest.raises(IdentityError,match='STALE_REVISION'):await svc(w).close_windows(w.ids['t1'],batch(w,[a,b]))
    assert (await w.session.get(BookingWindow,a)).status=='published'
    assert await count(w,Booking)==1
    await svc(w).close_windows(w.ids['t1'],batch(w,[a]))
    assert (await w.session.get(BookingWindow,b)).status=='consumed' and await count(w,Booking)==1

async def test_bulk_http_scope_bounds_and_duplicates(world):
    w=world;a=await window(w);data=batch(w,[a]).model_dump(mode='json')
    async with client(w,'t2') as c:
        assert (await c.post('/teacher-planning/booking-windows/close',json=data,headers=HEADERS)).status_code==404
    async with client(w,'s1') as c:
        assert (await c.post('/teacher-planning/booking-windows/close',json=data,headers=HEADERS)).status_code in (403,404)
    async with client(w,'t1') as c:
        assert (await c.post('/teacher-planning/booking-windows/close',json={**data,'items':data['items']*2},headers=HEADERS)).status_code==422
        assert (await c.post('/teacher-planning/booking-windows/close',json={**data,'items':[]},headers=HEADERS)).status_code==422
        assert (await c.post('/teacher-planning/booking-windows/close',json=data,headers=HEADERS)).status_code==200

async def test_bulk_receipt_failure_rolls_back_all_windows(world,monkeypatch):
    w=world;a=await window(w);b=await window(w,START+timedelta(hours=1));service=svc(w)
    original=service.repo.stage
    def fail(model,**values):
        if model is IdentityOperation:raise RuntimeError('synthetic receipt failure')
        return original(model,**values)
    monkeypatch.setattr(service.repo,'stage',fail)
    with pytest.raises(RuntimeError,match='synthetic receipt failure'):await service.close_windows(w.ids['t1'],batch(w,[a,b]))
    for id in (a,b):assert (await w.session.get(BookingWindow,id)).status=='published'

async def test_bulk_close_confirm_race_one_winner(world):
    w=world;a=await window(w);kid=await child(w);handle=await prepared(w,kid,a)
    async def close():
        async with w.db.factory() as s:return await svc(w,s).close_windows(w.ids['t1'],batch(w,[a]))
    async def book():
        async with w.db.factory() as s:return await svc(w,s).confirm_booking(confirm(kid,handle))
    results=await asyncio.gather(close(),book(),return_exceptions=True)
    assert sum(not isinstance(r,Exception) for r in results)==1
    await w.session.rollback();row=await w.session.get(BookingWindow,a)
    if row.status=='closed':assert await count(w,Booking)==0
    else:assert row.status=='consumed' and await count(w,Booking)==1
