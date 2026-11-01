"""Derived completion has matching list filters and never writes on GET."""
from datetime import UTC, datetime, timedelta
import pytest
from sqlalchemy import update, select
from src.modules.lessons.models import Lesson
from src.tools.synthetic_files import pdf_bytes
from tests.modules.auth.test_t06_permissions import world, auth

@pytest.mark.asyncio
async def test_automatic_completion_and_filters_do_not_write(client_for_tests,world,session_db):
    w=world;c=client_for_tests; lid=w['lessons'][0].id
    for stored, at, effective in [('scheduled',datetime.now(UTC)-timedelta(hours=2),'completed'),
            ('scheduled',datetime.now(UTC)+timedelta(hours=2),'scheduled'),
            ('cancelled',datetime.now(UTC)-timedelta(hours=2),'cancelled'),
            ('completed',datetime.now(UTC)+timedelta(hours=2),'completed')]:
        await session_db.execute(update(Lesson).where(Lesson.id==lid).values(status=stored,scheduled_at=at,duration_minutes=55));await session_db.commit()
        before=(await session_db.execute(select(Lesson.status,Lesson.updated_at).where(Lesson.id==lid))).one()
        for actor in ['t1','s1']:
            r=await c.get(f'/lessons/{lid}',headers=auth(w['accounts'][actor][1]))
            assert r.status_code==200,r.text
            assert r.json()['status']==effective
            r=await c.get('/lessons',headers=auth(w['accounts'][actor][1]),params={'course_id':w['courses'][0].id,'status':effective})
            assert r.status_code==200 and r.json()['total']==1,r.text
        after=(await session_db.execute(select(Lesson.status,Lesson.updated_at).where(Lesson.id==lid))).one()
        assert before==after

@pytest.mark.asyncio
async def test_four_material_files_per_recipient(client_for_tests,world):
    c=client_for_tests;w=world
    params={'lesson_id':w['lessons'][0].id,'student_user_id':w['accounts']['s1'][0].id}
    # world has one existing lecture.
    for i in range(3):
        r=await c.post('/lectures',headers=auth(w['accounts']['t1'][1]),data=params,files={'file':(f'{i}.pdf',pdf_bytes(),'application/pdf')})
        assert r.status_code==201,r.text
    r=await c.post('/lectures',headers=auth(w['accounts']['t1'][1]),data=params,files={'file':('fifth.pdf',pdf_bytes(),'application/pdf')})
    assert r.status_code==409 and r.json()['code']=='lecture_limit'
    r=await c.get('/lectures',headers=auth(w['accounts']['s1'][1]),params=params)
    assert r.json()['total']==4
