"""Executed in a clean subprocess, never imported by pytest collection."""

import asyncio
import importlib.abc
import io
import os
from pathlib import Path
import runpy
import sched
import socket
import sys
import tempfile
import threading
import urllib.request

# Resolve stdlib's temp directory before the strict file-write tripwire. Its
# one-time writable-directory probe is not an adapter/global JSON write.
tempfile.gettempdir()


class ForbiddenEffect(RuntimeError):
    pass


class ImportGuard(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if any(fullname == prefix or fullname.startswith(prefix + ".") for prefix in (
            "vk_api", "google", "gspread", "dotenv", "requests", "httpx",
            "src.core.config", "src.core.database", "VK_math_bot", "bot",
        )):
            raise ForbiddenEffect("Forbidden import: " + fullname)


def audit(name, args):
    if name.startswith("socket.") or name in ("subprocess.Popen", "os.system", "os.fork", "os.posix_spawn"):
        raise ForbiddenEffect("Forbidden network/process effect")
    if name == "open" and isinstance(args[0], (str, bytes, os.PathLike)):
        path = Path(os.fsdecode(args[0])).absolute()
        synthetic = any(part.startswith("lgg-f011-synthetic-") for part in path.parts)
        filename = path.name.lower()
        if filename.startswith(".env") or "credential" in filename or filename.endswith(".json") and not synthetic:
            raise ForbiddenEffect("Forbidden environment/JSON access")
        mode, flags = args[1], args[2]
        writing = (isinstance(mode, str) and any(char in mode for char in "wax+")) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
        if writing and not synthetic:
            raise ForbiddenEffect("Write outside temporary fixture workspace")


def no_scheduler(*args, **kwargs):
    raise ForbiddenEffect("Global reminder/scheduler forbidden")


sys.meta_path.insert(0, ImportGuard())
sys.addaudithook(audit)
threading.Thread.start = no_scheduler
sched.scheduler.enter = no_scheduler
sched.scheduler.enterabs = no_scheduler
asyncio.BaseEventLoop.call_later = no_scheduler

# Import after isolation is active; real environment/config/DB modules forbidden.
from src.modules.integrations_vk import fixtures as f
from src.modules.integrations_vk.offline import OfflineAdapter, OfflineConfig, TemporaryJsonStore


def must_block(operation):
    try:
        operation()
    except ForbiddenEffect:
        return
    raise AssertionError("Tripwire failed to catch a forbidden effect")


must_block(lambda: socket.create_connection(("127.0.0.1", 9)))
must_block(lambda: urllib.request.urlopen("https://example.invalid"))
must_block(lambda: open(".env"))
must_block(lambda: io.open("credentials.json"))
must_block(lambda: Path("global.json").write_text("{}"))
must_block(lambda: os.open("global.json", os.O_CREAT | os.O_WRONLY))
must_block(lambda: threading.Timer(0, lambda: None).start())
must_block(lambda: sched.scheduler().enter(0, 1, lambda: None))
must_block(lambda: __import__("vk_api"))
must_block(lambda: __import__("src.core.config"))

with TemporaryJsonStore() as store:
    platform = f.FixturePlatform()
    adapter = OfflineAdapter(OfflineConfig("offline"), store, f.FakeClock(), platform)
    commands = [
        ({"action": "menu_open"}, f.CHILD, "message_new"),
        ({"action": "profile_submit", "first_name": "Пример", "last_name": "Синтетический", "grade": 8}, f.CHILD, "message_new"),
        ({"action": "parent_candidate", "child_subject": "synthetic-child", "first_name": "Пример", "last_name": "Синтетический", "grade": None}, f.PARENT, "message_new"),
        ({"action": "confirm_booking", "handle": "fixture-handle", "operation_id": "00000000-0000-4000-8000-000000000001", "expected_revision": 1}, f.CHILD, "message_event"),
        ({"action": "permission_changed", "allowed": True}, f.CHILD, "message_allow"),
        ({"action": "permission_changed", "allowed": False}, f.CHILD, "message_deny"),
    ]
    for sequence, (command, actor, kind) in enumerate(commands, 1):
        raw = f.event(command, actor=actor, kind=kind, sequence=sequence)
        trusted = (f.GROUP, actor, actor)
        key = adapter.admit(raw, trusted=trusted)
        assert adapter.resume(key)["status"] == 202
        assert adapter.admit(raw, trusted=trusted) == key
        f.FakeVK().send(actor, "Synthetic fixture")
        f.FakeSheets().write(f.SHEET, [["synthetic"]])
    restarted = OfflineAdapter(OfflineConfig("offline"), store, f.FakeClock(), platform)
    assert restarted.resume(key)["status"] == 202
    assert len(platform.inbox) == len(commands)

sys.argv = ["integrations_vk", "--mode", "offline"]
runpy.run_module("src.modules.integrations_vk", run_name="__main__")
for argv in (["integrations_vk"], ["integrations_vk", "--mode", "live"]):
    sys.argv = argv
    try:
        runpy.run_module("src.modules.integrations_vk", run_name="__main__")
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("Entrypoint accepted missing/unknown config")
assert not any(name.startswith(("src.core.config", "src.core.database", "vk_api", "google", "gspread")) for name in sys.modules)
print("isolation PASS")
