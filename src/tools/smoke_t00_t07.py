"""Real HTTP acceptance on isolated lgg-dev. No schema reset; purge own new course only.

Run after dev migrations: MODE=DEV .venv/bin/python -m src.tools.smoke_t00_t07
Credentials are saved locally in ignored .env.audit-access (0600), never printed.
"""
import asyncio
import json
import hashlib
from io import BytesIO
from PIL import Image
import os
import sys
import secrets
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from typing import Any
from uuid import uuid4

import httpx
from passlib.context import CryptContext
from sqlalchemy import text

from src.core.config import create_config
import src.modules.db_models  # noqa: F401
from src.modules.users.bootstrap_dto import BootstrapInput
from src.modules.users.bootstrap_service import bootstrap_admin

ROOT = Path(__file__).resolve().parents[2]


async def main() -> None:
    config = create_config(media_root=ROOT / 'media-audit-client')
    env = config.env
    if (env.db_host, env.db_port, env.db_name, env.db_user) != (
        '127.0.0.1', '55431', 'lgg_dev', 'lgg_dev_app') or env.mode == 'TEST':
        raise RuntimeError('Refusing any target except isolated lgg-dev')
    credentials_path = ROOT / '.env.audit-access'
    if credentials_path.exists():
        credentials = json.loads(credentials_path.read_text())
    else:
        credentials = {'admin_username': 'audit_admin_' + uuid4().hex[:8],
                       'admin_password': secrets.token_urlsafe(24)}
        fd = os.open(credentials_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(credentials, stream)
    try:
        async with config.db_connection.session_local() as session:
            target = (await session.execute(text('SELECT current_database(), current_user'))).one()
            if tuple(target) != ('lgg_dev', 'lgg_dev_app'):
                raise RuntimeError('Database identity mismatch')
            await bootstrap_admin(session, BootstrapInput(
                username=credentials['admin_username'], email='audit-admin@example.com',
                password=credentials['admin_password']), CryptContext(schemes=['bcrypt']))
    finally:
        await config.db_connection.engine.dispose()

    checks: list[str] = []
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8018', timeout=30) as client:
        async def call(label: str, method: str, path: str, actor: dict[str, Any] | None = None,
                       expected: int | tuple[int, ...] = 200, **kwargs: Any) -> Any:
            headers = {'Authorization': 'Bearer ' + actor['access_token']} if actor else {}
            response = await client.request(method, path, headers=headers, **kwargs)
            if response.status_code not in ((expected,) if isinstance(expected, int) else expected):
                raise RuntimeError(f'{label}: expected {expected}, got {response.status_code}; response omitted to protect secrets')
            if response.headers.get('content-type', '').startswith('application/json'):
                data = response.json()
                if isinstance(data, dict) and 'hashed_password' in data:
                    raise RuntimeError(f'{label}: password hash leaked')
            else:
                data = response.content
            checks.append(label)
            print(f'PASS {len(checks)} {label}', flush=True)
            return data

        async def login(username: str, password: str) -> dict[str, str]:
            return await call('login ' + username, 'POST', '/auth/login',
                              data={'username': username, 'password': password})

        admin = await login(credentials['admin_username'], credentials['admin_password'])
        run = uuid4().hex[:8]
        password = secrets.token_urlsafe(24)

        async def account(role: str, creator: dict[str, str], suffix: str) -> tuple[dict[str, Any], dict[str, str]]:
            name = f'audit_{run}_{suffix}'
            user = await call('create pending ' + suffix, 'POST', '/auth/register', creator,
                              json={'username': name, 'role': role, 'first_name': 'Synthetic', 'last_name': suffix})
            await call('pending login denied ' + suffix, 'POST', '/auth/login', expected=401,
                       data={'username': name, 'password': password})
            token = parse_qs(urlsplit(user['activation_link']).fragment)['token'][0]
            body = {'token': token, 'purpose': 'invite', 'new_password': password}
            await call('activate ' + suffix, 'POST', '/account_invitations/consume', json=body)
            await call('activation replay denied ' + suffix, 'POST', '/account_invitations/consume', expected=401, json=body)
            return user, await login(name, password)

        teacher_a, a = await account('teacher', admin, 'teacher_a')
        teacher_b, b = await account('teacher', admin, 'teacher_b')
        student, s = await account('student', a, 'student')
        rotated = await call('refresh rotation', 'POST', '/auth/refresh_tokens', json={'refresh_token': s['refresh_token']})
        await call('refresh replay denied', 'POST', '/auth/refresh_tokens', expected=401, json={'refresh_token': s['refresh_token']})
        await call('replay revokes descendant', 'POST', '/auth/refresh_tokens', expected=401, json={'refresh_token': rotated['refresh_token']})
        s = await login(student['username'], password)
        await call('teacher cannot create teacher', 'POST', '/auth/register', a, expected=403,
                   json={'username': 'denied_' + run, 'role': 'teacher', 'first_name': 'No', 'last_name': 'No'})
        course = await call('create course A', 'POST', '/courses', a, expected=201,
                            json={'name': 'Synthetic audit ' + run, 'slug': 'audit-' + run})
        cid = course['id']
        avatar = await call('standard avatar PATCH', 'PATCH', f'/courses/{cid}', a,
                            json={'avatar_type': 'mathematics'})
        assert avatar['avatar_type'] == 'mathematics' and avatar['avatar_path'] is None
        await call('student cannot create course', 'POST', '/courses', s, expected=403,
                   json={'name': 'No', 'slug': 'no-' + run})
        await call('teacher B cannot enroll in A course', 'POST', f'/courses/{cid}/students', b, expected=404,
                   json={'student_user_id': student['id']})
        await call('enroll student', 'POST', f'/courses/{cid}/students', a, expected=201,
                   json={'student_user_id': student['id']})
        await call('student reads course', 'GET', f'/courses/{cid}', s)
        await call('teacher B direct course denied', 'GET', f'/courses/{cid}', b, expected=404)
        listed = await call('teacher B scoped course list', 'GET', '/courses', b)
        assert cid not in [item['id'] for item in listed['items']]
        await call('admin links student to teacher B', 'POST', '/teacher_students', admin,
                   json={'teacher_user_id': teacher_b['id'], 'student_user_id': student['id']})
        await call('linked teacher B still cannot read A course', 'GET', f'/courses/{cid}', b, expected=404)
        course_b = await call('create course B', 'POST', '/courses', b, expected=201,
                              json={'name': 'Synthetic B ' + run, 'slug': 'audit-b-' + run})
        await call('teacher B enrolls shared student', 'POST', f"/courses/{course_b['id']}/students", b,
                   expected=201, json={'student_user_id': student['id']})
        lesson = await call('create lesson with automatic recipient', 'POST', '/lessons', a, expected=201,
                            json={'course_id': cid, 'title': 'Synthetic lesson', 'scheduled_at': '2026-10-20T12:00:00Z', 'duration_minutes': 55})
        lid = lesson['id']
        await call('duplicate automatic recipient denied', 'POST', f'/lessons/{lid}/students', a, expected=409,
                   json={'student_user_id': student['id']})
        await call('student reads lesson', 'GET', f'/lessons/{lid}', s)
        await call('teacher B lesson denied', 'GET', f'/lessons/{lid}', b, expected=404)
        hw = await call('create synthetic homework', 'POST', '/homeworks', a, expected=201,
                        data={'lesson_id': lid, 'student_user_id': student['id'], 'title': 'Synthetic homework'})
        await call('student reads homework', 'GET', '/homeworks/my', s)
        image = BytesIO()
        Image.new('RGB', (64, 64), 'white').save(image, format='PNG')
        lecture = await call('upload and convert synthetic image', 'POST', '/lectures', a, expected=201,
                             data={'lesson_id': lid, 'student_user_id': student['id']},
                             files={'file': ('synthetic.png', image.getvalue(), 'image/png')})
        file_url = f"/lectures/{lecture['id']}/file?lesson_id={lid}&student_user_id={student['id']}"
        pdf = await call('student downloads PDF', 'GET', file_url, s)
        assert pdf.startswith(b'%PDF')
        await call('other teacher direct file denied', 'GET', file_url, b, expected=404)
        archived = await call('archive course', 'DELETE', f'/courses/{cid}', a)
        assert archived['is_deleted'] and archived['slug'] == course['slug']
        assert await call('archived PDF remains downloadable', 'GET', file_url, s) == pdf
        await call('student reads archived lesson', 'GET', f'/lessons/{lid}', s)
        await call('archive blocks lesson write', 'PATCH', f'/lessons/{lid}', a, expected=403, json={'title': 'Denied'})
        await call('teacher restore denied', 'POST', f'/courses/{cid}/restore', a, expected=403)
        restored = await call('admin restores course', 'POST', f'/courses/{cid}/restore', admin)
        assert not restored['is_deleted']
        await call('restored course permits write', 'PATCH', f'/lessons/{lid}', a, json={'title': 'Restored lesson'})
        await call('archive lesson separately', 'DELETE', f'/lessons/{lid}', a)
        await call('archive course again', 'DELETE', f'/courses/{cid}', a)
        await call('restore course again', 'POST', f'/courses/{cid}/restore', admin)
        separate = await call('separate lesson archive preserved', 'GET', f'/lessons/{lid}', s)
        assert separate['is_deleted']
        await call('admin restores lesson', 'POST', f'/lessons/{lid}/restore', admin)
        purge = {'confirm_course_id': cid, 'confirm_name': course['name']}
        await call('teacher purge denied', 'POST', f'/courses/{cid}/purge', a, expected=403, json=purge)
        await call('wrong purge confirmation denied', 'POST', f'/courses/{cid}/purge', admin, expected=400,
                   json={**purge, 'confirm_name': 'WRONG'})
        purged = await call('purge only this run synthetic course', 'POST', f'/courses/{cid}/purge', admin, json=purge)
        assert purged['cleanup']['failed'] == 0 and purged['cleanup']['completed'] > 0
        await call('purged file inaccessible', 'GET', file_url, admin, expected=404)
        await call('purged course absent', 'GET', f'/courses/{cid}', admin, expected=(403, 404))
        await call('other course survives purge', 'GET', f"/courses/{course_b['id']}", s)
        patch_archive = await call('legacy PATCH archives with timestamp', 'PATCH', f"/courses/{course_b['id']}", b,
                                   json={'is_deleted': True})
        assert patch_archive['deleted_at']
        await call('restore PATCH archived course', 'POST', f"/courses/{course_b['id']}/restore", admin)
        retained_lesson = await call('create retained synthetic lesson', 'POST', '/lessons', b, expected=201,
                                    json={'course_id': course_b['id'], 'title': 'Restart check', 'scheduled_at': '2026-10-22T12:00:00Z'})
        await call('retained automatic recipient duplicate denied', 'POST', f"/lessons/{retained_lesson['id']}/students", b, expected=409,
                   json={'student_user_id': student['id']})
        retained = await call('upload retained synthetic file', 'POST', '/lectures', b, expected=201,
                              data={'lesson_id': retained_lesson['id'], 'student_user_id': student['id']},
                              files={'file': ('retained.png', image.getvalue(), 'image/png')})
        retained_url = f"/lectures/{retained['id']}/file?lesson_id={retained_lesson['id']}&student_user_id={student['id']}"
        retained_pdf = await call('read retained PDF', 'GET', retained_url, s)
        credentials.update({'retained_file_url': retained_url, 'retained_sha256': hashlib.sha256(retained_pdf).hexdigest()})
        await call('logout', 'POST', '/auth/logout', s, json={'refresh_token': s['refresh_token']})
        await call('logout refresh denied', 'POST', '/auth/refresh_tokens', expected=401, json={'refresh_token': s['refresh_token']})
        credentials.update({'teacher_a_username': teacher_a['username'], 'teacher_b_username': teacher_b['username'],
                            'student_username': student['username'], 'synthetic_password': password, 'course_b_id': course_b['id']})
        credentials_path.write_text(json.dumps(credentials))
        print(f'HTTP acceptance passed: {len(checks)} requests; credentials stored locally, not printed.')


async def verify_retained() -> None:
    """Read-only persistence check after Docker restart; only stored synthetic IDs."""
    credentials = json.loads((ROOT / '.env.audit-access').read_text())
    async with httpx.AsyncClient(base_url='http://127.0.0.1:8018', timeout=30) as client:
        response = await client.post('/auth/login', data={
            'username': credentials['student_username'], 'password': credentials['synthetic_password']})
        if response.status_code != 200:
            raise RuntimeError('Retained synthetic student login failed')
        headers = {'Authorization': 'Bearer ' + response.json()['access_token']}
        course = await client.get(f"/courses/{credentials['course_b_id']}", headers=headers)
        pdf = await client.get(credentials['retained_file_url'], headers=headers)
        if (course.status_code != 200 or pdf.status_code != 200 or
                hashlib.sha256(pdf.content).hexdigest() != credentials['retained_sha256']):
            raise RuntimeError('Retained course/PDF differs after restart')
        print('PASS restart persistence: login, course and identical PDF (SHA256), 3 HTTP requests')


if __name__ == '__main__':
    if sys.argv[1:] == ['--verify-retained']:
        asyncio.run(verify_retained())
    elif sys.argv[1:]:
        raise SystemExit('Usage: python -m src.tools.smoke_t00_t07 [--verify-retained]')
    else:
        asyncio.run(main())
