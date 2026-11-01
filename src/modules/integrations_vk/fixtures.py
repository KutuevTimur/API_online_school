"""Fixed synthetic transports. No URLs, tokens, SDKs or domain implementation."""

import json
from dataclasses import dataclass

from .events import canonical


GROUP = 900001
CHILD = 900101
PARENT = 900102
TRUSTED_CHILD = (GROUP, CHILD, CHILD)
TRUSTED_PARENT = (GROUP, PARENT, PARENT)
SHEET = "synthetic-f011-sheet"


@dataclass
class FakeClock:
    now: float = 1793577600.0

    def timestamp(self) -> float:
        return self.now


class FakeVK:
    def __init__(self):
        self.sent = []

    def send(self, peer_id: int, text: str) -> None:
        if type(peer_id) is not int or peer_id not in (CHILD, PARENT):
            raise ValueError("Synthetic peer allowlist")
        self.sent.append((peer_id, text))


class FakeSheets:
    def __init__(self):
        self.writes = []

    def write(self, target: str, values: list) -> None:
        if target != SHEET:
            raise ValueError("Synthetic sheet allowlist")
        self.writes.append((target, json.loads(json.dumps(values))))


class FixturePlatform:
    """In-memory HTTP contract fixture; accepted is not booking confirmation.

    Holds upstream dedupe across an adapter restart/timeout. No User, grant,
    Booking, Lesson, receipt or permission implementation is provided here.
    """

    def __init__(self):
        self.inbox = {}
        self.calls = []
        self.timeout_after_accept = False

    def request(self, method: str, path: str, body: dict) -> dict:
        if (method, path) != ("POST", "/integrations/vk/inbox"):
            raise ValueError("Fixture HTTP route allowlist")
        payload = json.loads(canonical(body))
        self.calls.append((method, path, payload))
        key = payload["event_key"]
        duplicate = key in self.inbox
        if duplicate and self.inbox[key] != payload:
            raise ValueError("PAYLOAD_MISMATCH")
        self.inbox[key] = payload
        if self.timeout_after_accept:
            self.timeout_after_accept = False
            raise TimeoutError("Synthetic timeout after fixture admission")
        return {"status": 202, "body": {"inbox_id": "fixture-" + key,
                "state": "duplicate" if duplicate else "accepted"}}


def event(command: dict, *, kind="message_new", actor=CHILD, sequence=1) -> bytes:
    payload = {"type": kind, "group_id": GROUP, "api_version": "5.199",
               "actor_subject": actor, "peer_id": actor,
               "occurred_at": "2026-11-02T00:00:00Z", "command": command}
    if kind == "message_new":
        payload["conversation_message_id"] = sequence
    else:
        payload["upstream_event_id"] = "fixture-event-" + str(sequence)
    return canonical(payload).encode()
