"""T10 synthetic HTTP acceptance. Fixed loopback; no reset, purge or credential output."""
import asyncio
import hashlib
from src.tools.synthetic_files import pdf_bytes
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
            r = await client.request(method, path,
                headers={'Authorization': 'Bearer '+token} if token else {}, **kwargs)
            if r.status_code != expected:
                raise RuntimeError(f'{label}: expected {expected}, got {r.status_code}; body omitted')
            count += 1
            print(f'PASS {count} {label}', flush=True)
            return r.json() if 'application/json' in r.headers.get('content-type', '') else r.content

        tokens = {}
        for actor, key in [('a', 'teacher_a_username'), ('b', 'teacher_b_username'), ('s', 'student_username')]:
            result = await call('login '+actor, 'POST', '/auth/login', data={
                'username': saved[key], 'password': saved['synthetic_password']})
            tokens[actor] = result['access_token']
        a, b, s = (tokens[x] for x in ('a', 'b', 's'))
        teacher = await call('reviewer public identity', 'GET', '/users/me', a)
        if '--verify-retained' in sys.argv:
            record = saved['t10']
            url = f"/submissions/{record['submission_id']}?homework_id={record['homework_id']}"
            result = await call('checked result persists', 'GET', url, s)
            assert result['grade'] == 0 and result['version'] == record['version']
            assert result['checked_by'] == teacher['id'] and result['teacher_comment'] == 'T10 final review'
            queue = await call('checked absent after restart', 'GET', '/submissions/review-queue', a,
                params={'course_id': record['course_id']})
            assert queue['total'] == 0
            retained = await call('file persists', 'GET',
                f"/submissions/{record['submission_id']}/files/{record['file_id']}?homework_id={record['homework_id']}", s)
            assert hashlib.sha256(retained).hexdigest() == record.get('file_sha256', hashlib.sha256(b'%PDF T10 answer').hexdigest())
            await call('OpenAPI available', 'GET', '/openapi.json')
            print(f'T10 restart persistence PASS: {count} requests', flush=True)
            return
        uid = (await call('student identity', 'GET', '/users/me', s))['id']
        run = uuid4().hex[:8]
        course = await call('synthetic course', 'POST', '/courses', a, 201,
            json={'name': 'T10 '+run, 'slug': 't10-'+run})
        cid = course['id']
        await call('enroll', 'POST', f'/courses/{cid}/students', a, 201, json={'student_user_id': uid})
        lesson = await call('personal lesson', 'POST', '/lessons', a, 201,
            json={'course_id': cid, 'title': 'T10 review', 'scheduled_at': '2028-07-01T12:00:00Z'})
        hw = await call('homework', 'POST', '/homeworks', a, 201, data={
            'lesson_id': lesson['id'], 'student_user_id': uid, 'title': 'T10 synthetic homework'})
        hid = hw['id']
        draft = await call('draft with file', 'POST', f'/homeworks/{hid}/submissions', s, 201,
            files={'files': ('answer.pdf', pdf_bytes('T10 answer'), 'application/pdf')})
        sid = draft['id']; url = f'/submissions/{sid}'; q = f'?homework_id={hid}'
        await call('draft review denied', 'PATCH', url+'/teacher'+q, a, 409,
            json={'grade': 0, 'expected_version': draft['version']})
        sent = await call('submit', 'POST', url+'/submit'+q, s)
        queue = await call('queue context and version', 'GET', '/submissions/review-queue', a,
            params={'course_id': cid, 'student_user_id': uid})
        assert queue['total'] == 1 and queue['items'][0]['version'] == sent['version']
        assert queue['items'][0]['student_user_id'] == uid and queue['items'][0]['lesson_id'] == lesson['id']
        empty = await call('empty offset preserves total', 'GET', '/submissions/review-queue', a,
            params={'course_id': cid, 'offset': 99})
        assert empty['items'] == [] and empty['total'] == 1
        foreign = await call('other teacher queue scoped', 'GET', '/submissions/review-queue', b, params={'course_id': cid})
        assert foreign['total'] == 0
        await call('student queue denied', 'GET', '/submissions/review-queue', s, 403)
        await call('other teacher review denied', 'PATCH', url+'/teacher'+q, b, 404,
            json={'grade': 4, 'expected_version': sent['version']})
        await call('missing version denied', 'PATCH', url+'/teacher'+q, a, 422, json={'grade': 3})
        await call('fractional grade denied', 'PATCH', url+'/teacher'+q, a, 422,
            json={'grade': 3.5, 'expected_version': sent['version']})
        edited = await call('student correction', 'PATCH', url+'/student'+q, s,
            data={'text_content': 'T10 corrected answer'})
        await call('stale review denied', 'PATCH', url+'/teacher'+q, a, 409,
            json={'grade': 0, 'expected_version': sent['version']})
        queue = await call('queue shows latest text and version', 'GET', '/submissions/review-queue', a,
            params={'course_id': cid})
        assert queue['items'][0]['version'] == edited['version'] and queue['items'][0]['text_content'] == 'T10 corrected answer'
        checked = await call('zero grade final review', 'PATCH', url+'/teacher'+q, a,
            json={'grade': 0, 'expected_version': edited['version'], 'teacher_comment': 'T10 final review'})
        assert checked['checked_by'] == teacher['id'] and checked['checked_at'].endswith('Z')
        assert (await call('student sees result', 'GET', url+q, s)) == checked
        queue = await call('checked removed from queue', 'GET', '/submissions/review-queue', a, params={'course_id': cid})
        assert queue['total'] == 0
        await call('checked review immutable', 'PATCH', url+'/teacher'+q, a, 403,
            json={'grade': 5, 'expected_version': checked['version']})
        await call('checked answer immutable', 'PATCH', url+'/student'+q, s, 403, data={'text_content': 'change'})
        assert await call('checked file download', 'GET', url+f"/files/{checked['files'][0]['id']}"+q, s) == pdf_bytes('T10 answer')
        schema = await call('OpenAPI contract', 'GET', '/openapi.json')
        required = schema['components']['schemas']['UpdateSubmissionTeacherRequestDTO']['required']
        assert set(required) == {'grade', 'expected_version'}
        saved['t10'] = dict(course_id=cid, lesson_id=lesson['id'], homework_id=hid,
            submission_id=sid, version=checked['version'], file_id=checked['files'][0]['id'], file_sha256=hashlib.sha256(pdf_bytes('T10 answer')).hexdigest())
        access.write_text(json.dumps(saved, indent=2)); access.chmod(0o600)
        print(f'T10 HTTP PASS: {count} requests', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
