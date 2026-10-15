"""Synthetic T09 HTTP smoke; fixed loopback, no reset/purge, credentials never printed."""
import asyncio
import json
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
            r = await client.request(method,path,
                headers={'Authorization':'Bearer '+token} if token else {}, **kwargs)
            if r.status_code != expected:
                raise RuntimeError(f'{label}: expected {expected}, got {r.status_code}; body omitted')
            count += 1
            print(f'PASS {count} {label}',flush=True)
            return r.json() if 'application/json' in r.headers.get('content-type','') else r.content

        actors={}
        for name,userkey in [('a','teacher_a_username'),('b','teacher_b_username'),('s','student_username')]:
            r=await call('login '+name,'POST','/auth/login',data={
                'username':saved[userkey],'password':saved['synthetic_password']})
            actors[name]=r['access_token']
        a,b,s=(actors[x] for x in ('a','b','s'))
        identity=await call('student identity','GET','/users/me',s)
        uid=identity['id']; run=uuid4().hex[:8]
        course=await call('new synthetic course','POST','/courses',a,201,json={'name':'T09 '+run,'slug':'t09-'+run})
        cid=course['id']
        await call('enrollment','POST',f'/courses/{cid}/students',a,201,json={'student_user_id':uid})
        lesson=await call('personal lesson','POST','/lessons',a,201,json={
            'course_id':cid,'title':'T09 response lifecycle','scheduled_at':'2028-06-10T12:00:00Z'})
        homework=await call('homework','POST','/homeworks',a,201,data={
            'lesson_id':lesson['id'],'student_user_id':uid,'title':'T09 synthetic answer','deadline':'2026-01-01T00:00:00Z'})
        hid=homework['id']; base=f'/homeworks/{hid}/submissions'
        # Each HTTP request obtains an independent backend AsyncSession.
        async def create():
            return await client.post(base,headers={'Authorization':'Bearer '+s})
        pair=await asyncio.gather(create(),create())
        assert sorted(r.status_code for r in pair)==[201,409]
        print('PASS concurrent HTTP create: one 201, one 409',flush=True)
        draft=next(r.json() for r in pair if r.status_code==201)
        sid=draft['id']; url=f'/submissions/{sid}'; q=f'?homework_id={hid}'
        assert draft['submitted_at'] is None and draft['version']==1
        await call('empty submit rejected','POST',url+'/submit'+q,s,422)
        first=await call('first file','PATCH',url+'/student'+q,s,
            files={'files':('answer.pdf',b'%PDF T09 first','application/pdf')})
        fid=first['files'][0]['id']
        second=await call('append same filename','PATCH',url+'/student'+q,s,
            files={'files':('answer.pdf',b'%PDF T09 second','application/pdf')})
        assert len(second['files'])==2 and fid in [f['id'] for f in second['files']]
        assert await call('old bytes preserved','GET',url+f'/files/{fid}'+q,s)==b'%PDF T09 first'
        sent=await call('file-only late submit','POST',url+'/submit'+q,s)
        assert sent['status']=='submitted'
        assert await call('idempotent submit','POST',url+'/submit'+q,s)==sent
        updated=await call('edit submitted text','PATCH',url+'/student'+q,s,
            data={'text_content':'T09 corrected answer','expected_version':sent['version']})
        await call('stale edit denied','PATCH',url+'/student'+q,s,409,
            data={'text_content':'stale','expected_version':sent['version']})
        swapped=await call('swap single file','PUT',url+f'/files/{fid}'+q,s,
            files={'file':('answer.pdf',b'%PDF T09 replacement','application/pdf')})
        other=next(f['id'] for f in second['files'] if f['id']!=fid)
        assert other in [f['id'] for f in swapped['files']] and fid not in [f['id'] for f in swapped['files']]
        await call('remove one file','DELETE',url+f'/files/{other}'+q,s)
        await call('foreign teacher hidden','GET',url+q,b,404)
        checked=await call('teacher checks submitted','PATCH',url+'/teacher'+q,a,
                           json={'status':'checked','grade':5,'teacher_comment':'T09 synthetic checked'})
        remaining=checked['files'][0]['id']
        await call('checked text immutable','PATCH',url+'/student'+q,s,403,data={'text_content':'forbidden'})
        await call('checked append immutable','PATCH',url+'/student'+q,s,403,
                   files={'files':('a.pdf',b'forbidden','application/pdf')})
        await call('checked file delete denied','DELETE',url+f'/files/{remaining}'+q,s,403)
        await call('checked swap denied','PUT',url+f'/files/{remaining}'+q,s,403,
                   files={'file':('a.pdf',b'forbidden','application/pdf')})
        await call('checked answer delete denied','DELETE',url+q,s,403)
        await call('teacher cannot reopen checked','PATCH',url+'/teacher'+q,a,403,json={'status':'draft'})
        await call('no resubmission','POST',base,s,409)
        assert await call('preserved checked download','GET',url+f'/files/{remaining}'+q,s)==b'%PDF T09 replacement'
        saved['t09']={'course_id':cid,'lesson_id':lesson['id'],'homework_id':hid,
                       'submission_id':sid,'file_id':remaining,'version':checked['version']}
        access.write_text(json.dumps(saved,indent=2)); access.chmod(0o600)
        print(f'T09 HTTP PASS: {count} requests plus independent concurrent create pair',flush=True)


if __name__ == '__main__':
    asyncio.run(main())
