"""Local synthetic T13 HTTP acceptance; no secrets or payloads in output."""
import asyncio
import json
from pathlib import Path
import sys
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
                       expected: int = 200, **kwargs: Any) -> dict:
            nonlocal count
            r = await client.request(method, path, headers={
                'Authorization': 'Bearer '+token} if token else {}, **kwargs)
            if r.status_code != expected:
                raise RuntimeError(f'{label}: expected {expected}, got {r.status_code}; body omitted')
            count += 1
            print(f'PASS {count} {label}', flush=True)
            return r.json()
        tokens = {}
        for actor, key in [('a','teacher_a_username'), ('b','teacher_b_username'), ('s','student_username')]:
            tokens[actor] = (await call('login '+actor, 'POST', '/auth/login', data={
                'username':saved[key], 'password':saved['synthetic_password']}))['access_token']
        a,b,s = (tokens[k] for k in ('a','b','s'))
        if '--verify-retained' in sys.argv:
            record = saved['t13']
            for kind, token in [('submitted',a), ('checked',s)]:
                n = record[kind]
                rows = await call(kind+' notification retained','GET','/notifications',token)
                assert any(row['id'] == n for row in rows['items'])
                target = await call(kind+' target retained','GET',f'/notifications/{n}/target',token)
                assert target['available'] and target['object_id'] == record['submission_id']
            page = await call('read time retained','GET','/notifications',s)
            assert next(n for n in page['items'] if n['id'] == record['checked'])['read_at'] == record['read_at']
            await call('foreign target still hidden','GET',f"/notifications/{record['submitted']}/target",b,404)
            print(f'T13 restart PASS: {count} requests',flush=True)
            return
        uid = (await call('student identity','GET','/users/me',s))['id']
        run = uuid4().hex[:8]
        cid = (await call('synthetic course','POST','/courses',a,201,json={'name':'T13 '+run,'slug':'t13-'+run}))['id']
        await call('enroll','POST',f'/courses/{cid}/students',a,201,json={'student_user_id':uid})
        lid = (await call('lesson','POST','/lessons',a,201,json={'course_id':cid,'title':'T13 notifications','scheduled_at':'2028-09-01T12:00:00Z'}))['id']
        hid = (await call('assign homework','POST','/homeworks',a,201,data={'lesson_id':lid,'student_user_id':uid,'title':'T13 synthetic'}))['id']
        rows = await call('assignment recipient inbox','GET','/notifications',s)
        assigned = next(n for n in rows['items'] if n['object_type'] == 'homework' and n['object_id'] == hid)
        assert assigned['event_type'] == 'homework_assigned'
        await call('other teacher cannot mark student event','PATCH',f"/notifications/{assigned['id']}/read",b,404)
        sid = (await call('draft','POST',f'/homeworks/{hid}/submissions',s,201,data={'text_content':'T13 synthetic answer'}))['id']
        q=f'?homework_id={hid}'; url=f'/submissions/{sid}'
        sent = await call('submit','POST',url+'/submit'+q,s)
        await call('retry submit','POST',url+'/submit'+q,s)
        teacher = await call('teacher inbox','GET','/notifications',a)
        matches = [n for n in teacher['items'] if n['object_id'] == sid and n['event_type'] == 'solution_submitted']
        assert len(matches) == 1
        submitted = matches[0]['id']
        target = await call('teacher target authorized','GET',f'/notifications/{submitted}/target',a)
        assert target['available'] and target['homework_id'] == hid
        edited = await call('edit submitted','PATCH',url+'/student'+q,s,data={'text_content':'Updated synthetic answer'})
        assert edited['version'] == sent['version']+1
        teacher = await call('edit does not spam','GET','/notifications',a)
        assert len([n for n in teacher['items'] if n['object_id'] == sid and n['event_type'] == 'solution_submitted']) == 1
        await call('review','PATCH',url+'/teacher'+q,a,json={'expected_version':edited['version'],'grade':5})
        student = await call('checked inbox','GET','/notifications',s)
        checked = next(n['id'] for n in student['items'] if n['object_id'] == sid and n['event_type'] == 'solution_checked')
        read = await call('mark read','PATCH',f'/notifications/{checked}/read',s)
        retry = await call('retry mark read','PATCH',f'/notifications/{checked}/read',s)
        assert retry['read_at'] == read['read_at']
        await call('move lesson','PATCH',f'/lessons/{lid}',a,json={'scheduled_at':'2028-09-02T12:00:00Z'})
        await call('cancel lesson','PATCH',f'/lessons/{lid}',a,json={'status':'cancelled'})
        await call('retry cancel','PATCH',f'/lessons/{lid}',a,json={'status':'cancelled'})
        student = await call('lesson events once each','GET','/notifications',s)
        assert {n['event_type'] for n in student['items'] if n['object_type']=='lesson' and n['object_id']==lid} == {'lesson_rescheduled','lesson_cancelled'}
        await call('teacher audit denied','GET','/audit-events',a,403)
        await call('anonymous inbox denied','GET','/notifications',None,401)
        saved['t13'] = dict(course_id=cid,homework_id=hid,submission_id=sid,submitted=submitted,checked=checked,read_at=read['read_at'])
        access.write_text(json.dumps(saved,ensure_ascii=False,indent=2)+'\n')
        access.chmod(0o600)
        print(f'T13 HTTP PASS: {count} requests',flush=True)


if __name__ == '__main__':
    asyncio.run(main())
