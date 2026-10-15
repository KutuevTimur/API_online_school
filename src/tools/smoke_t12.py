"""Synthetic T12 HTTP smoke; no resets or secrets in output."""
import asyncio
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
from uuid import uuid4

import httpx
from PIL import Image
import pillow_heif

from src.tools.synthetic_files import pdf_bytes

ROOT = Path(__file__).resolve().parents[2]


async def main() -> None:
    access = ROOT / '.env.audit-access'
    saved = json.loads(access.read_text())
    count = 0
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8018', timeout=45) as client:
        async def call(label, method, path, token=None, expected=200, extra_headers=None, **kwargs):
            nonlocal count
            headers = {'Authorization': 'Bearer ' + token} if token else {}
            headers.update(extra_headers or {})
            response = await client.request(method, path, headers=headers, **kwargs)
            if response.status_code != expected:
                raise RuntimeError(f'{label}: expected {expected}, got {response.status_code}; body omitted')
            count += 1
            print(f'PASS {count} {label}', flush=True)
            return response
        tokens = {}
        for name, key in [('a', 'teacher_a_username'), ('b', 'teacher_b_username'), ('s', 'student_username')]:
            r = await call('login ' + name, 'POST', '/auth/login', data={
                'username': saved[key], 'password': saved['synthetic_password']})
            tokens[name] = r.json()['access_token']
        a,b,s = (tokens[k] for k in ('a','b','s'))
        if '--verify-retained' in sys.argv:
            record = saved['t12']
            r = await call('new asset survives restart', 'GET', record['url'], s)
            assert hashlib.sha256(r.content).hexdigest() == record['sha256']
            assert r.headers['cache-control'] == 'private, no-store'
            await call('other teacher remains denied', 'GET', record['url'], b, 404)
            await call('OpenAPI', 'GET', '/openapi.json')
            print(f'T12 restart PASS: {count} requests', flush=True)
            return
        uid = (await call('student identity', 'GET', '/users/me', s)).json()['id']
        budget=(await call('student quota report', 'GET', f'/users/{uid}/storage', s)).json()
        assert budget['limit_bytes']==1024**3
        await call('other teacher cannot inspect global student quota','GET',f'/users/{uid}/storage',b,403)
        run = uuid4().hex[:8]
        cid = (await call('course', 'POST', '/courses', a, 201, json={'name':'T12 ' + run, 'slug':'t12-' + run})).json()['id']
        await call('enroll', 'POST', f'/courses/{cid}/students', a, 201, json={'student_user_id':uid})
        lid = (await call('lesson', 'POST', '/lessons', a, 201,
                         json={'course_id':cid, 'title':'T12 storage', 'scheduled_at':'2028-08-01T12:00:00Z'})).json()['id']
        form = {'lesson_id':lid, 'student_user_id':uid}
        source = pdf_bytes('T12 original')
        lecture = (await call('PDF lecture with hostile display name', 'POST', '/lectures', a, 201,
            data=form, files={'file':('../../safe.pdf',source,'text/html')})).json()
        assert lecture['original_file_name'] == 'safe.pdf' and 'file_path' not in str(lecture)
        path = f"/lectures/{lecture['id']}/file?lesson_id={lid}&student_user_id={uid}"
        r = await call('lecture download', 'GET', path, s)
        assert r.content == source and r.headers['x-content-type-options'] == 'nosniff'
        r = await call('authorized PDF Range', 'GET', path, s, 206, extra_headers={'Range':'bytes=0-4'})
        assert r.content == b'%PDF-' and r.headers['content-range'] == f'bytes 0-4/{len(source)}'
        await call('anonymous Range denied', 'GET', path, None, 401, extra_headers={'Range':'bytes=0-4'})
        await call('foreign Range denied', 'GET', path, b, 404, extra_headers={'Range':'bytes=0-4'})
        await call('invalid range', 'GET', path, s, 416, extra_headers={'Range':'bytes=999999-'})
        await call('renamed executable rejected', 'POST', '/lectures', a, 400,
                   data=form, files={'file':('fake.pdf',b'MZ payload','application/pdf')})
        await call('office disabled in MVP', 'POST', '/lectures', a, 400,
                   data=form, files={'file':('source.docx',b'PK','application/octet-stream')})
        await call('stream byte limit', 'POST', '/lectures', a, 413,
                   data=form, files={'file':('large.pdf',b'x' * (20 * 1024 * 1024 + 1),'application/pdf')})
        hw = (await call('homework PDF', 'POST', '/homeworks', a, 201,
            data={**form,'title':'T12 guarded uploads'}, files={'file':('homework.pdf',source,'application/pdf')})).json()
        hid = hw['id']
        draft = (await call('answer PDF', 'POST', f'/homeworks/{hid}/submissions', s, 201,
            files={'files':('answer.pdf',source,'application/pdf')})).json()
        sid = draft['id']; url = f'/submissions/{sid}'; q = f'?homework_id={hid}'
        file_id = draft['files'][0]['id']
        original_url = url+f'/files/{file_id}'+q
        assert (await call('answer original bytes', 'GET', original_url, s)).content == source
        await call('other teacher file_id denied', 'GET', original_url, b, 404)
        pillow_heif.register_heif_opener()
        image = Image.new('RGB',(80,120),'white')
        buf = BytesIO(); image.save(buf, format='HEIF')
        photo=await call('HEIC decoder in Linux image', 'PATCH', url+'/student'+q, s,
                   files={'files':('phone.heic',buf.getvalue(),'image/heic')})
        photo_id=photo.json()['files'][-1]['id']
        normalized=await call('HEIC download is WebP','GET',url+f'/files/{photo_id}'+q,s)
        assert normalized.headers['content-type']=='image/webp'
        with Image.open(BytesIO(normalized.content)) as pixels:
            assert pixels.size==(80,120) and not pixels.getexif()
        usage=(await call('quota includes managed files','GET',f'/users/{uid}/storage',s)).json()
        assert usage['used_bytes']>budget['used_bytes']
        stress=BytesIO(); Image.new('RGB',(8064,6048),'white').save(stress,'JPEG')
        large_photo=await call('48 MP photo through bounded Linux worker','PATCH',url+'/student'+q,s,
            files={'files':('48mp.jpg',stress.getvalue(),'image/jpeg')})
        large_id=large_photo.json()['files'][-1]['id']
        result=await call('48 MP result has correct dimensions','GET',url+f'/files/{large_id}'+q,s)
        with Image.open(BytesIO(result.content)) as pixels:assert pixels.size==(2560,1920)
        boundary=BytesIO();Image.new('RGB',(32,32),'white').save(boundary,'JPEG')
        exact=boundary.getvalue()+b'\0'*(20*1024*1024-len(boundary.getvalue()))
        await call('exact 20 MiB source accepted','PATCH',url+'/student'+q,s,
            files={'files':('boundary.jpg',exact,'image/jpeg')})
        r = await call('fill count to ten', 'PATCH', url+'/student'+q, s,
                       files=[('files',('same.pdf',source,'application/pdf'))] * 6)
        assert len(r.json()['files']) == 10
        await call('eleventh file rejected', 'PATCH', url+'/student'+q, s, 400,
                   files={'files':('extra.pdf',source,'application/pdf')})
        r = await call('swap at count ten', 'PUT', url+f'/files/{file_id}'+q, s,
                       files={'file':('replacement.pdf',source,'application/pdf')})
        kept_id = r.json()['files'][-1]['id']
        kept_url = url+f'/files/{kept_id}'+q
        assert (await call('swapped bytes', 'GET', kept_url, s)).content == source
        await call('OpenAPI', 'GET', '/openapi.json')
        saved['t12'] = {'url':kept_url, 'sha256':hashlib.sha256(source).hexdigest(),
                        'course_id':cid, 'homework_id':hid, 'submission_id':sid}
        access.write_text(json.dumps(saved,indent=2)); access.chmod(0o600)
        print(f'T12 HTTP PASS: {count} requests', flush=True)


if __name__ == '__main__':
    asyncio.run(main())
