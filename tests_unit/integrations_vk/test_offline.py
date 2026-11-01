"""F01.1: standalone tests, no tests/conftest.py or database imports."""

import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


@pytest.fixture
def api(monkeypatch):
    # Installed before importing any adapter/fixture module.
    def forbidden(*args, **kwargs):
        raise AssertionError("Offline side effect forbidden")

    import socket
    import threading
    import sched
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(threading.Thread, "start", forbidden)
    monkeypatch.setattr(sched.scheduler, "enter", forbidden)
    offline = importlib.import_module("src.modules.integrations_vk.offline")
    fixtures = importlib.import_module("src.modules.integrations_vk.fixtures")
    return offline, fixtures


@pytest.fixture
def harness(api):
    mod, f = api
    with mod.TemporaryJsonStore() as store:
        clock, platform = f.FakeClock(), f.FixturePlatform()
        adapter = mod.OfflineAdapter(mod.OfflineConfig("offline"), store, clock, platform)
        yield adapter, platform, clock, f


@pytest.mark.parametrize("command,actor,kind", [
    ({"action": "menu_open"}, 900101, "message_new"),
    ({"action": "profile_submit", "first_name": " Пример ", "last_name": "Синтетический", "grade": 8}, 900101, "message_new"),
    ({"action": "parent_candidate", "child_subject": "synthetic-child", "first_name": "Пример", "last_name": "Синтетический", "grade": None}, 900102, "message_new"),
    ({"action": "confirm_booking", "handle": "fixture-handle", "operation_id": "00000000-0000-4000-8000-000000000001", "expected_revision": 1}, 900101, "message_event"),
    ({"action": "permission_changed", "allowed": True}, 900101, "message_allow"),
    ({"action": "permission_changed", "allowed": False}, 900101, "message_deny"),
])
def test_scenarios_through_fixture_http(harness, command, actor, kind):
    adapter, platform, clock, f = harness
    raw = f.event(command, actor=actor, kind=kind)
    key = adapter.admit(raw, trusted=(f.GROUP, actor, actor))
    assert not platform.calls
    assert adapter.store.read()[key]["accepted_at"] == clock.now
    response = adapter.resume(key)
    assert response["status"] == 202 and response["body"]["state"] == "accepted"
    assert len(platform.inbox) == 1
    forwarded = platform.calls[0][2]
    assert forwarded["command"]["action"] == command["action"]
    # Exercise fake outbound boundaries explicitly, not automatic Sheets fallback.
    vk, sheets = f.FakeVK(), f.FakeSheets()
    vk.send(actor, "Synthetic fixture accepted")
    sheets.write(f.SHEET, [["synthetic", command["action"]]])
    assert vk.sent == [(actor, "Synthetic fixture accepted")]
    assert sheets.writes == [(f.SHEET, [["synthetic", command["action"]]])]


def test_replay_and_payload_collision(harness):
    adapter, platform, clock, f = harness
    raw = f.event({"action": "menu_open"})
    key = adapter.admit(raw, trusted=f.TRUSTED_CHILD)
    first = adapter.resume(key)
    clock.now += 600
    assert adapter.admit(raw, trusted=f.TRUSTED_CHILD) == key
    assert adapter.resume(key) == first
    assert len(platform.calls) == 1
    with pytest.raises(ValueError, match="PAYLOAD_MISMATCH"):
        adapter.admit(f.event({"action": "profile_submit", "first_name": "Другой", "last_name": "Пример", "grade": 7}), trusted=f.TRUSTED_CHILD)
    assert len(platform.calls) == 1


def test_identical_text_with_new_event_identity_is_not_replay(harness):
    adapter, platform, _, f = harness
    keys = [adapter.admit(f.event({"action": "menu_open"}, sequence=n),
                          trusted=f.TRUSTED_CHILD) for n in (1, 2)]
    assert keys[0] != keys[1]
    for key in keys:
        adapter.resume(key)
    assert len(platform.inbox) == 2


def test_failed_fixture_http_preserves_pending_inbox(harness):
    adapter, platform, _, f = harness
    key = adapter.admit(f.event({"action": "menu_open"}), trusted=f.TRUSTED_CHILD)
    adapter.platform = type("BadHTTP", (), {"request": lambda *_: {"status": 503}})()
    with pytest.raises(ValueError, match="Invalid fixture platform response"):
        adapter.resume(key)
    assert adapter.store.read()[key]["response"] is None
    adapter.platform = platform
    assert adapter.resume(key)["status"] == 202


def test_atomic_json_failure_keeps_previous_checkpoint(harness, monkeypatch):
    adapter, platform, _, f = harness
    key = adapter.admit(f.event({"action": "menu_open"}), trusted=f.TRUSTED_CHILD)
    original_replace = Path.replace

    def crash(*_):
        raise OSError("Synthetic crash before atomic replace")

    monkeypatch.setattr(Path, "replace", crash)
    with pytest.raises(OSError, match="Synthetic crash"):
        adapter.resume(key)
    assert adapter.store.read()[key]["response"] is None
    monkeypatch.setattr(Path, "replace", original_replace)
    assert adapter.resume(key)["body"]["state"] == "duplicate"
    assert len(platform.inbox) == 1


@pytest.mark.parametrize("after_accept", [False, True])
def test_crash_restart_from_disk(harness, api, after_accept):
    adapter, platform, clock, f = harness
    mod, _ = api
    key = adapter.admit(f.event({"action": "menu_open"}), trusted=f.TRUSTED_CHILD)
    if after_accept:
        platform.timeout_after_accept = True
        with pytest.raises(TimeoutError):
            adapter.resume(key)
    assert adapter.store.read()[key]["response"] is None
    # New adapter, same disk-backed temporary state; no in-memory dedupe in adapter.
    restarted = mod.OfflineAdapter(mod.OfflineConfig("offline"), adapter.store, clock, platform)
    result = restarted.resume(key)
    assert result["body"]["state"] == ("duplicate" if after_accept else "accepted")
    assert len(platform.inbox) == 1
    assert restarted.resume(key) == result
    assert len(platform.calls) == (2 if after_accept else 1)


@pytest.mark.parametrize("change,error", [
    ({"group_id": 123}, "SCOPE_DENIED"),
    ({"actor_subject": 123}, "SCOPE_DENIED"),
    ({"peer_id": 123}, "SCOPE_DENIED"),
    ({"type": "unknown"}, "UNSUPPORTED_EVENT"),
    ({"conversation_message_id": 0}, "EVENT_KEY_UNAVAILABLE"),
    ({"conversation_message_id": None}, "EVENT_KEY_UNAVAILABLE"),
    ({"occurred_at": "yesterday"}, "INVALID_REQUEST"),
    ({"occurred_at": "20261102T000000Z"}, "INVALID_REQUEST"),
    ({"conversation_message_id": 0, "upstream_event_id": "fixture-forged"}, "EVENT_KEY_UNAVAILABLE"),
    ({"extra": "forged"}, "INVALID_REQUEST"),
    ({"command": {"action": "menu_open", "teacher_user_id": 1}}, "INVALID_REQUEST"),
    ({"command": {"action": "parent_candidate", "child_subject": "x", "first_name": "x", "last_name": "y", "grade": True}}, "INVALID_REQUEST"),
    ({"command": {"action": "confirm_booking", "handle": "x", "operation_id": "invalid", "expected_revision": 1}}, "INVALID_REQUEST"),
])
def test_forged_and_malformed_before_effect(harness, change, error):
    adapter, platform, _, f = harness
    payload = json.loads(f.event({"action": "menu_open"}))
    payload.update(change)
    with pytest.raises(ValueError, match=error):
        adapter.admit(json.dumps(payload).encode(), trusted=f.TRUSTED_CHILD)
    assert adapter.store.read() == {} and platform.calls == []


@pytest.mark.parametrize("raw", [b"{", b"[]", b"null", b"\xff", b" " * 65537,
                                      b'{"type":NaN}',
                                      b'{"type":"message_new","type":"message_event"}'])
def test_bad_json(harness, raw):
    adapter, platform, _, f = harness
    with pytest.raises(ValueError):
        adapter.admit(raw, trusted=f.TRUSTED_CHILD)
    assert adapter.store.read() == {} and not platform.calls


@pytest.mark.parametrize("kind", ["message_event", "message_allow", "message_deny"])
def test_missing_reliable_identity_quarantined(harness, kind):
    adapter, platform, _, f = harness
    command = {"action": "menu_open"} if kind == "message_event" else {"action": "permission_changed", "allowed": kind == "message_allow"}
    payload = json.loads(f.event(command, kind=kind))
    del payload["upstream_event_id"]
    with pytest.raises(ValueError, match="EVENT_KEY_UNAVAILABLE"):
        adapter.admit(json.dumps(payload).encode(), trusted=f.TRUSTED_CHILD)
    assert not platform.calls and adapter.store.read() == {}


def test_allow_event_cannot_forge_deny_or_grant(harness):
    adapter, platform, _, f = harness
    raw = f.event({"action": "permission_changed", "allowed": False}, kind="message_allow")
    with pytest.raises(ValueError, match="INVALID_REQUEST"):
        adapter.admit(raw, trusted=f.TRUSTED_CHILD)
    assert not platform.calls and adapter.store.read() == {}


@pytest.mark.parametrize("config", [{"mode": "live"}, {"mode": "UNKNOWN"},
                                      {"mode": "offline", "startup_ping": True},
                                      {"mode": "offline", "scheduler": True}])
def test_configuration_fails_before_effect(api, config):
    mod, f = api
    with pytest.raises(ValueError):
        mod.OfflineAdapter(mod.OfflineConfig(**config), None, f.FakeClock(), f.FixturePlatform())


def test_fake_target_allowlists(api):
    _, f = api
    vk, sheets, platform = f.FakeVK(), f.FakeSheets(), f.FixturePlatform()
    for target in (123, str(f.CHILD), True):
        with pytest.raises(ValueError):
            vk.send(target, "blocked")
    with pytest.raises(ValueError):
        sheets.write("production", [])
    with pytest.raises(ValueError):
        platform.request("POST", "https://example.invalid", {})
    assert vk.sent == [] and sheets.writes == [] and platform.calls == []


def test_json_guard_and_cleanup(api, tmp_path):
    mod, _ = api
    store = mod.TemporaryJsonStore()
    root, original = store._root, store._path
    try:
        store._path = tmp_path / "global.json"
        with pytest.raises(ValueError, match="JSON outside"):
            store.write({})
        assert not store._path.exists()
        store._path = original
        outside = tmp_path / "untouched.json"
        outside.write_text('{"untouched":true}')
        original.symlink_to(outside)
        with pytest.raises(ValueError):
            store.write({})
        assert outside.read_text() == '{"untouched":true}'
        original.unlink()
        original.write_text("broken")
        with pytest.raises(ValueError):
            store.read()
    finally:
        store.close()
    assert not root.exists()


def test_clean_process_import_entrypoint_and_tripwires(tmp_path):
    """Audit tripwires precede import; no env/SDK/DB/network/global JSON access."""
    probe = Path(__file__).with_name("isolation_probe.py")
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run([sys.executable, str(probe)], cwd=tmp_path,
                            env={"PYTHONPATH": str(root), "PYTHONDONTWRITEBYTECODE": "1"},
                            capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "isolation PASS" in result.stdout
