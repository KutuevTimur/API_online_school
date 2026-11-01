"""Single-process offline harness; never registered in the application startup.

Only synthetic, temporary state. This is not a production inbox/outbox, worker,
permission service or booking implementation. All domain responses are fixtures.
"""

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .events import canonical, normalize
from .ports import Clock, PlatformTransport


@dataclass(frozen=True)
class OfflineConfig:
    mode: str
    startup_ping: bool = False
    scheduler: bool = False

    def validate(self):
        if self.mode != "offline" or self.startup_ping is not False or self.scheduler is not False:
            raise ValueError("Only offline mode without startup effects is supported")


class TemporaryJsonStore:
    """Owns its path; no supplied filename, production path or env discovery."""

    def __init__(self):
        self._temporary = tempfile.TemporaryDirectory(prefix="lgg-f011-synthetic-")
        self._root = Path(self._temporary.name).resolve()
        self._path = self._root / "inbox.json"

    def _guard(self):
        root = Path(self._temporary.name)
        if root.is_symlink() or root.resolve() != self._root or not root.is_dir():
            raise ValueError("Temporary workspace unavailable")
        if self._path != self._root / "inbox.json" or self._path.is_symlink():
            raise ValueError("JSON outside temporary workspace")
        if (self._root / "inbox.tmp").is_symlink():
            raise ValueError("Unsafe temporary JSON")

    def read(self) -> dict:
        self._guard()
        if not self._path.exists():
            return {}
        # Corrupt state fails closed rather than resetting dedupe.
        state = json.loads(self._path.read_text(encoding="utf-8"))
        if not isinstance(state, dict) or any(
            not isinstance(row, dict) or set(row) != {"hash", "event", "accepted_at", "response"}
            for row in state.values()
        ):
            raise ValueError("Invalid fixture inbox")
        return state

    def write(self, state: dict):
        self._guard()
        path = self._root / "inbox.tmp"
        with path.open("w", encoding="utf-8") as stream:
            stream.write(canonical(state))
            stream.flush()
            os.fsync(stream.fileno())
        path.replace(self._path)

    def close(self):
        self._temporary.cleanup()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()


class OfflineAdapter:
    def __init__(self, config: OfflineConfig, store: TemporaryJsonStore,
                 clock: Clock, platform: PlatformTransport):
        config.validate()  # Before loading state or invoking any injected effect.
        self.store, self.clock, self.platform = store, clock, platform

    def admit(self, raw: bytes, *, trusted: tuple[int, int, int]) -> str:
        event = normalize(raw, trusted=trusted)
        key = event["event_key"]
        digest = hashlib.sha256(canonical(event).encode()).hexdigest()
        state = self.store.read()
        if key in state:
            if state[key]["hash"] != digest:
                raise ValueError("PAYLOAD_MISMATCH")
            return key
        state[key] = {"hash": digest, "event": event,
                      "accepted_at": self.clock.timestamp(), "response": None}
        self.store.write(state)  # Checkpoint before fixture HTTP submission.
        return key

    def resume(self, key: str) -> dict:
        state = self.store.read()
        row = state[key]
        if row["response"] is None:
            response = self.platform.request("POST", "/integrations/vk/inbox", row["event"])
            if (not isinstance(response, dict) or response.get("status") != 202
                    or not isinstance(response.get("body"), dict)
                    or response["body"].get("state") not in ("accepted", "duplicate")):
                raise ValueError("Invalid fixture platform response")
            row["response"] = response
            self.store.write(state)
        return row["response"]
