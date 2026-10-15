"""T11 synthetic loopback HTTP acceptance; no DB reset/purge or credential output."""
import asyncio
import json
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

ROOT = Path(__file__).resolve().parents[2]


async def main() -> None:
    access = ROOT / '.env.audit-access'
    saved = json.loads(access.read_text())
    count = 0
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8018', timeout=30) as client:
        async def call(label: str, method: str, path: str, token: str | None = None,
                       expected: int = 200, **kwargs: Any) -> Any:
            nonlocal count
            response = await client.request(method, path,
                headers={'Authorization': 'Bearer '+token} if token else {}, **kwargs)
            if response.status_code != expected:
                raise RuntimeError(f'{label}: expected {expected}, got {response.status_code}; body omitted')
            count += 1
            print(f'PASS {count} {label}', flush=True)
            return response.json() if 'application/json' in response.headers.get('content-type', '') else response.content

        tokens = {}
        for actor, key in [('a', 'teacher_a_username'), ('b', 'teacher_b_username'), ('s', 'student_username')]:
            result = await call('login '+actor, 'POST', '/auth/login', data={
                'username': saved[key], 'password': saved['synthetic_password']})
            tokens[actor] = result['access_token']
        a,b,s = (tokens[x] for x in ('a','b','s'))
        if '--verify-retained' in sys.argv:
            record = saved['t11']; hid = record['homework_id']
            history = await call('frozen placement history persists', 'GET', f'/homeworks/{hid}/placements', s)
            assert history == record['history']
            result = await call('single effective homework persists', 'GET', '/homeworks/my', s)
            hw = next(h for h in result if h['id'] == hid)
            assert hw['placement_id'] == record['placement_id'] and hw['deadline'] == record['deadline']
            assert hw['submission_status'] == 'checked'
            queue = await call('checked absent from queue after restart', 'GET', '/submissions/review-queue', a,
                               params={'course_id':record['course_id']})
            assert queue['total'] == 0
            await call('OpenAPI', 'GET', '/openapi.json')
            print(f'T11 restart persistence PASS: {count} requests', flush=True)
            return
        uid = (await call('student identity', 'GET', '/users/me', s))['id']
        run = uuid4().hex[:8]
        course = await call('synthetic course', 'POST', '/courses', a, 201,
                            json={'name':'T11 '+run,'slug':'t11-'+run})
        cid = course['id']
        await call('enroll', 'POST', f'/courses/{cid}/students', a, 201, json={'student_user_id':uid})
        async def lesson(day: int) -> dict[str, Any]:
            return await call('lesson '+str(day), 'POST', '/lessons', a, 201,
                json={'course_id':cid,'title':'T11 lesson '+str(day),'scheduled_at':f'2026-10-{day:02}T12:00:00Z'})
        origin = await lesson(19)
        hw = await call('homework without next lesson', 'POST', '/homeworks', a, 201,
                        data={'lesson_id':origin['id'],'student_user_id':uid,'title':'T11 automatic deadline'})
        hid = hw['id']; assert hw['deadline'] is None
        second = await lesson(22)
        path = f'/homeworks/{hid}/placements'
        result = await call('new next sets deadline', 'GET', path, s)
        assert result[0]['due_lesson_id'] == second['id']
        third = await lesson(26)
        placement = await call('debt refers to original homework', 'POST', f'/homeworks/{hid}/debts', a, 201,
                               json={'lesson_id':second['id']})
        assert placement['homework_id'] == hid and placement['due_lesson_id'] == third['id']
        again = await call('repeat debt idempotent', 'POST', f'/homeworks/{hid}/debts', a, 201,
                           json={'lesson_id':second['id']})
        assert again['id'] == placement['id']
        await call('other teacher cannot add debt', 'POST', f'/homeworks/{hid}/debts', b, 404,
                   json={'lesson_id':third['id']})
        await call('student cannot add debt', 'POST', f'/homeworks/{hid}/debts', s, 403,
                   json={'lesson_id':third['id']})
        await call('move next to 27th', 'PATCH', f"/lessons/{third['id']}", a,
                   json={'scheduled_at':'2026-10-27T12:00:00Z'})
        result = await call('debt deadline follows next', 'GET', path, s)
        assert result[-1]['due_at'] == '2026-10-27T12:00:00Z'
        assert [e['due_at'] for e in result[-1]['events']] == ['2026-10-26T12:00:00Z','2026-10-27T12:00:00Z']
        result = await call('old lesson retains original deadline', 'GET', '/homeworks', s,
                            params={'lesson_id':origin['id'],'student_user_id':uid})
        assert result[0]['deadline'] == '2026-10-22T12:00:00Z'
        result = await call('debt lesson has assignment flag', 'GET', f"/lessons/{second['id']}", s)
        assert result['has_homework'] is True
        draft = await call('one shared answer', 'POST', f'/homeworks/{hid}/submissions', s, 201,
                           data={'text_content':'T11 answer'})
        sid = draft['id']; url = f'/submissions/{sid}'; query = f'?homework_id={hid}'
        sent = await call('submit', 'POST', url+'/submit'+query, s)
        result = await call('one review queue item', 'GET', '/submissions/review-queue', a, params={'course_id':cid})
        assert result['total'] == 1 and result['items'][0]['id'] == sid
        await call('check freezes deadlines', 'PATCH', url+'/teacher'+query, a,
                   json={'grade':4,'expected_version':sent['version']})
        frozen = await call('frozen journal', 'GET', path, s)
        assert all(p['frozen'] for p in frozen)
        await call('move next after check', 'PATCH', f"/lessons/{third['id']}", a,
                   json={'scheduled_at':'2026-10-28T12:00:00Z'})
        assert await call('checked history unchanged', 'GET', path, s) == frozen
        await call('checked cannot become debt', 'POST', f'/homeworks/{hid}/debts', a, 409,
                   json={'lesson_id':third['id']})
        result = await call('one homework with latest placement', 'GET', '/homeworks/my', s)
        entries = [h for h in result if h['id'] == hid]
        assert len(entries) == 1 and entries[0]['submission_status'] == 'checked'
        assert entries[0]['placement_kind'] == 'debt'
        await call('OpenAPI', 'GET', '/openapi.json')
        saved['t11'] = dict(course_id=cid,homework_id=hid,history=frozen,placement_id=placement['id'],
                            deadline=entries[0]['deadline'],submission_id=sid)
        access.write_text(json.dumps(saved,indent=2)); access.chmod(0o600)
        print(f'T11 HTTP PASS: {count} requests', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
