import asyncio
from pathlib import Path
from types import SimpleNamespace
import struct
import zlib

import pytest
from PIL import Image
from src.modules.handlers_files.handler_documents import HandlerDocuments
from src.modules.handlers_files.exception import InvalidDocumentFormat


def handler(tmp_path):
    return HandlerDocuments(SimpleNamespace(paths=SimpleNamespace(media=tmp_path)))


@pytest.mark.asyncio
async def test_timeout_and_cancel_kill_and_reap_process(tmp_path,monkeypatch):
    source=tmp_path/'photo.jpg';Image.new('RGB',(10,10),'white').save(source)
    service=handler(tmp_path);service.processing_timeout_seconds=.001
    real=asyncio.create_subprocess_exec;processes=[];created=asyncio.Event()
    async def spawn(*args,**kwargs):
        proc=await real(*args,**kwargs);processes.append(proc);created.set();return proc
    monkeypatch.setattr(asyncio,'create_subprocess_exec',spawn)
    with pytest.raises(InvalidDocumentFormat,match='30 seconds'):
        await service.inspect_document(source,'jpg')
    assert processes[-1].returncode is not None
    service.processing_timeout_seconds=30;created.clear()
    task=asyncio.create_task(service.inspect_document(source,'jpg'))
    await created.wait();task.cancel()
    with pytest.raises(asyncio.CancelledError):await task
    assert processes[-1].returncode is not None
    assert service.config._file_processing_semaphore._value==1


@pytest.mark.asyncio
async def test_huge_declared_dimensions_rejected_before_decode(tmp_path):
    source=tmp_path/'huge.png';Image.new('RGB',(10,10),'white').save(source)
    data=bytearray(source.read_bytes())
    data[16:24]=struct.pack('>II',10000,6000)
    data[29:33]=struct.pack('>I',zlib.crc32(data[12:29]) & 0xffffffff)
    source.write_bytes(data)
    with pytest.raises(InvalidDocumentFormat):await handler(tmp_path).inspect_document(source,'png')
