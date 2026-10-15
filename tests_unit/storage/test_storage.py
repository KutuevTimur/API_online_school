import asyncio
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest
from starlette.applications import Starlette
from starlette.requests import Request
from httpx import ASGITransport, AsyncClient
from starlette.routing import Route

from src.modules.storage.service import LocalStorage, LegacyStorage, UnsafeStorageKey, StorageLimitExceeded
from src.modules.storage.download import private_download, safe_display_name


class Stream:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.sizes = []

    async def read(self, size: int = -1) -> bytes:
        assert 0 < size <= 65536
        self.sizes.append(size)
        value, self.data = self.data[:size], self.data[size:]
        return value


@pytest.fixture
def storage(tmp_path):
    return LocalStorage(SimpleNamespace(media=tmp_path))


@pytest.mark.asyncio
async def test_contract_stream_hash_immutable_retry(storage):
    data = b'a' * 200000
    result = await storage.put(Stream(data), 'objects/abc', max_bytes=len(data))
    assert result.size == len(data)
    assert result.sha256 == hashlib.sha256(data).hexdigest()
    assert (await storage.stat('objects/abc')).size == len(data)
    async with storage.open('objects/abc') as file:
        assert file.read() == data
    with pytest.raises(FileExistsError):
        await storage.put(Stream(b'overwrite'), 'objects/abc', max_bytes=20)
    assert (storage.root / 'objects/abc').read_bytes() == data
    await storage.delete('objects/abc')
    await storage.delete('objects/abc')
    with pytest.raises(FileNotFoundError):
        await storage.stat('objects/abc')
    assert list((storage.root / 'objects').iterdir()) == []


@pytest.mark.parametrize('key', ['', '.', '..', '../secret', '/tmp/secret', 'a/../b', 'a//b',
                                    'a/./b', 'a/', 'a\\b', 'bad\x00key'])
@pytest.mark.asyncio
async def test_all_operations_reject_unsafe_keys(storage, key):
    with pytest.raises(UnsafeStorageKey):
        await storage.put(Stream(b'x'), key, max_bytes=10)
    with pytest.raises(UnsafeStorageKey):
        await storage.stat(key)
    with pytest.raises(UnsafeStorageKey):
        await storage.delete(key)


@pytest.mark.asyncio
async def test_limits_failure_cancel_do_not_publish(storage):
    with pytest.raises(StorageLimitExceeded):
        await storage.put(Stream(b'x' * 65537), 'limit', max_bytes=65536)
    class Broken(Stream):
        async def read(self, size=-1):
            if not self.data:
                raise OSError('disk/source failure')
            return await super().read(size)
    with pytest.raises(OSError):
        await storage.put(Broken(b'x'), 'broken', max_bytes=10)
    entered = asyncio.Event()
    class Hanging(Stream):
        async def read(self, size=-1):
            if not self.data:
                entered.set()
                await asyncio.Event().wait()
            return await super().read(size)
    task = asyncio.create_task(storage.put(Hanging(b'x'), 'cancelled', max_bytes=10))
    await entered.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert list(storage.root.iterdir()) == []


@pytest.mark.asyncio
async def test_symlink_file_and_ancestor_escape(storage, tmp_path):
    outside = tmp_path.parent / (tmp_path.name + '-outside')
    outside.mkdir()
    secret = outside / 'secret'
    secret.write_bytes(b'secret')
    (storage.root / 'link').symlink_to(outside, target_is_directory=True)
    (storage.root / 'file').symlink_to(secret)
    for key in ['link/secret', 'file']:
        with pytest.raises((OSError, UnsafeStorageKey)):
            await storage.stat(key)
        with pytest.raises((OSError, UnsafeStorageKey)):
            await storage.delete(key)
        with pytest.raises(OSError):
            await storage.put(Stream(b'attack'), key, max_bytes=10)
    assert secret.read_bytes() == b'secret'
    assert list(outside.iterdir()) == [secret]


@pytest.mark.asyncio
async def test_read_open_descriptor_not_replaced_path(storage):
    await storage.put(Stream(b'first'), 'object', max_bytes=10)
    async with storage.open('object') as file:
        (storage.root / 'object').unlink()
        (storage.root / 'object').write_bytes(b'second')
        assert file.read() == b'first'


@pytest.mark.asyncio
async def test_legacy_read_only_and_outside(storage):
    legacy = LegacyStorage(SimpleNamespace(media=storage.root))
    assert legacy.key(storage.root / 'old/file.pdf') == 'old/file.pdf'
    with pytest.raises(UnsafeStorageKey):
        legacy.key('/etc/passwd')
    with pytest.raises(TypeError):
        await legacy.put(Stream(b'x'), 'object', max_bytes=10)
    with pytest.raises(TypeError):
        await legacy.delete('object')


@pytest.mark.asyncio
async def test_download_ranges_headers_and_escape(storage):
    await storage.put(Stream(b'0123456789'), 'old.pdf', max_bytes=10)
    async def endpoint(request: Request):
        return await private_download(request, request.query_params.get('path', str(storage.root / 'old.pdf')),
                                      '../../имя\r\n.pdf')
    app = Starlette(routes=[Route('/download', endpoint)])
    app.state.config = SimpleNamespace(paths=SimpleNamespace(media=storage.root))
    async with AsyncClient(transport=ASGITransport(app=app), base_url='http://test') as client:
        response = await client.get('/download')
        assert response.content == b'0123456789'
        assert response.headers['cache-control'] == 'private, no-store'
        assert response.headers['x-content-type-options'] == 'nosniff'
        assert '%0D' not in response.headers['content-disposition']
        for value, expected in [('bytes=2-4', b'234'), ('bytes=-3', b'789'), ('bytes=7-', b'789')]:
            response = await client.get('/download', headers={'Range': value})
            assert response.status_code == 206 and response.content == expected
        for value in ['bytes=99-', 'bytes=4-1', 'bytes=-0', 'bytes=0-1,4-5', 'words=0-1']:
            response = await client.get('/download', headers={'Range': value})
            assert response.status_code == 416
        response = await client.get('/download', params={'path': '/etc/passwd'})
        assert response.status_code == 404
    assert safe_display_name('..\\bad\r\n.jpg') == 'bad.jpg'


@pytest.mark.asyncio
async def test_disk_full_does_not_publish_or_destroy_existing_object(storage,monkeypatch):
    import errno
    import os
    await storage.put(Stream(b'old'),'old',max_bytes=10)
    def full(*args,**kwargs):raise OSError(errno.ENOSPC,'synthetic disk full')
    with monkeypatch.context() as patch:
        patch.setattr(os,'link',full)
        with pytest.raises(OSError):await storage.put(Stream(b'new'),'new',max_bytes=10)
    assert (storage.root/'old').read_bytes()==b'old'
    assert sorted(p.name for p in storage.root.iterdir())==['old']
