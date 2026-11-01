"""Injected side effects; no default/live implementations in F01.1."""

from typing import Protocol


class Clock(Protocol):
    def timestamp(self) -> float: ...


class PlatformTransport(Protocol):
    def request(self, method: str, path: str, body: dict) -> dict: ...


class VKTransport(Protocol):
    def send(self, peer_id: int, text: str) -> None: ...


class SheetsTransport(Protocol):
    def write(self, target: str, values: list) -> None: ...
