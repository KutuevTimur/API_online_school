"""Real HTTP T08 check on synthetic lgg-dev; preserves created course for manual use.

Requires a successful smoke_t00_t07 run and its ignored .env.audit-access.
Only fixed loopback HTTP, no DB reset, no purge, no external meeting URL fetches.
"""
import asyncio
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[2]


async def main() -> None:
    credentials_path = ROOT / '.env.audit-access'
    credentials = json.loads(credentials_path.read_text())
    count = 0
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8018', timeout=30) as client:
        async def call(label: str, method: str, path: str, token: str | None = None,
                       expected: int = 200, **kwargs: Any) -> Any:
            nonlocal count
            response = await client.request(method, path,
                headers={'Authorization': 'Bearer ' + token} if token else {}, **kwargs)
            if response.status_code != expected:
                raise RuntimeError(f'{label}: expected {expected}, got {response.status_code}; response omitted')
            count += 1
            print(f'PASS {count} {label}', flush=True)
            return response.json() if 'application/json' in response.headers.get('content-type', '') else response.content

        actors = {}
        identities = {}
        for name, userkey, passkey in [('a','teacher_a_username','synthetic_password'),
                ('b','teacher_b_username','synthetic_password'), ('student','student_username','synthetic_password'),
                ('admin','admin_username','admin_password')]:
            data = await call('login ' + name, 'POST', '/auth/login', data={
                'username':credentials[userkey], 'password':credentials[passkey]})
            actors[name] = data['access_token']
            identities[name] = await call('identity ' + name, 'GET', '/users/me', actors[name])
        a, b, student, admin = [actors[name] for name in ('a','b','student','admin')]
        uid = identities['student']['id']
        run = uuid4().hex[:8]
        course = await call('course with permanent meeting URL', 'POST', '/courses', a, expected=201,
            json={'name':'T08 synthetic ' + run, 'slug':'t08-' + run, 'call_url':'https://example.com/t08-room'})
        cid = course['id']
        body = {'course_id':cid, 'title':'T08 first lesson', 'scheduled_at':'2028-02-10T15:00:00+03:00'}
        await call('empty course cannot create lesson', 'POST', '/lessons', a, expected=422, json=body)
        await call('enroll synthetic student', 'POST', f'/courses/{cid}/students', a, expected=201,
                   json={'student_user_id':uid})
        first = await call('atomic lesson and recipient', 'POST', '/lessons', a, expected=201, json=body)
        lid = first['id']
        assert first['duration_minutes'] == 55 and first['status'] == 'scheduled'
        assert first['scheduled_at'] == '2028-02-10T12:00:00Z' and first['warnings'] == []
        assert first['effective_call_url'] == course['call_url']
        await call('student immediately reads new lesson', 'GET', f'/lessons/{lid}', student)
        for name, token, expected in [('student',student,403),('admin',admin,403),('other teacher',b,404)]:
            await call(name + ' cannot change schedule', 'PATCH', f'/lessons/{lid}', token, expected=expected,
                       json={'status':'cancelled'})
        await call('other teacher direct lesson denied', 'GET', f'/lessons/{lid}', b, expected=404)
        second = await call('adjacent lesson allowed without warning', 'POST', '/lessons', a, expected=201,
                            json={**body, 'title':'T08 second lesson', 'scheduled_at':'2028-02-10T12:55:00Z'})
        assert not second['warnings']
        other = second['id']
        moved = await call('overlap saves with warning', 'PATCH', f'/lessons/{other}', a,
                           json={'scheduled_at':'2028-02-10T12:54:00Z'})
        assert moved['warnings'] == [{'code':'teacher_time_overlap','lesson_ids':[lid]}]
        await call('naive datetime rejected', 'PATCH', f'/lessons/{other}', a, expected=422,
                   json={'scheduled_at':'2028-02-10T12:54:00'})
        await call('zero duration rejected', 'PATCH', f'/lessons/{other}', a, expected=422,
                   json={'duration_minutes':0})
        await call('unsafe meeting URL rejected', 'PATCH', f'/lessons/{other}', a, expected=422,
                   json={'call_url_override':'javascript:alert(1)'})
        override = await call('one-off meeting link', 'PATCH', f'/lessons/{other}', a,
                              json={'call_url_override':'https://example.com/t08-one-off'})
        assert override['effective_call_url'] == 'https://example.com/t08-one-off'
        await call('change course meeting link', 'PATCH', f'/courses/{cid}', a,
                   json={'call_url':'https://example.com/t08-new-room'})
        fallback = await call('old lesson uses current course link', 'GET', f'/lessons/{lid}', student)
        assert fallback['effective_call_url'] == 'https://example.com/t08-new-room'
        override = await call('explicit override stays independent', 'GET', f'/lessons/{other}', student)
        assert override['effective_call_url'] == 'https://example.com/t08-one-off' and not override['warnings']
        cleared = await call('clear override restores fallback', 'PATCH', f'/lessons/{other}', a,
                             json={'call_url_override':None})
        assert cleared['effective_call_url'] == 'https://example.com/t08-new-room'
        homework = await call('create homework before cancellation', 'POST', '/homeworks', a, expected=201,
                              data={'lesson_id':lid, 'student_user_id':uid, 'title':'T08 preserved homework'})
        for status in ('cancelled', 'completed'):
            changed = await call('mark lesson ' + status, 'PATCH', f'/lessons/{lid}', a, json={'status':status})
            assert changed['status'] == status and not changed['is_deleted']
            material = await call('homework preserved after ' + status, 'GET', '/homeworks', student,
                                  params={'lesson_id':lid, 'student_user_id':uid})
            assert homework['id'] in [item['id'] for item in material]
        completed = await call('status filter before pagination', 'GET', '/lessons', student,
                               params={'course_id':cid, 'status':'completed', 'limit':1})
        assert completed['total'] == 1 and completed['items'][0]['id'] == lid
        moved = await call('move individual lesson', 'PATCH', f'/lessons/{lid}', a,
                           json={'scheduled_at':'2028-02-11T20:00:00+03:00'})
        assert moved['scheduled_at'] == '2028-02-11T17:00:00Z'
        other_lesson = await call('second lesson did not move', 'GET', f'/lessons/{other}', student)
        assert other_lesson['scheduled_at'] == '2028-02-10T12:54:00Z'
        await call('archive course', 'DELETE', f'/courses/{cid}', a)
        await call('archive blocks status mutation', 'PATCH', f'/lessons/{lid}', a, expected=403,
                   json={'status':'scheduled'})
        await call('admin restores archived course', 'POST', f'/courses/{cid}/restore', admin)
        preserved = await call('restore preserves completed status', 'GET', f'/lessons/{lid}', student)
        assert preserved['status'] == 'completed' and not preserved['is_deleted']
        credentials.update({'t08_course_id':cid, 't08_lesson_id':lid, 't08_other_lesson_id':other})
        credentials_path.write_text(json.dumps(credentials))
        print(f'T08 HTTP acceptance passed: {count} requests; synthetic course preserved, credentials not printed.')


if __name__ == '__main__':
    asyncio.run(main())
