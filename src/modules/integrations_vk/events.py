"""Strict normalized fixture envelope, not a parser/authenticator of raw VK events.

Raw SDK extraction and connector MAC admission belong to later stages. The
offline caller supplies an explicitly trusted fixture group/actor/peer tuple.
"""

import hashlib
import json
import re
from datetime import datetime
from uuid import UUID


class InvalidEvent(ValueError):
    pass


def canonical(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidEvent("INVALID_REQUEST")
        result[key] = value
    return result


def _non_json_constant(value):
    raise InvalidEvent("INVALID_REQUEST")


def normalize(raw: bytes, *, trusted: tuple[int, int, int]) -> dict:
    if not isinstance(raw, bytes) or len(raw) > 65536:
        raise InvalidEvent("INVALID_REQUEST")
    try:
        event = json.loads(raw, object_pairs_hook=_object, parse_constant=_non_json_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise InvalidEvent("INVALID_REQUEST") from exc
    required = {"type", "group_id", "api_version", "actor_subject", "peer_id",
                "occurred_at", "command"}
    optional = {"conversation_message_id", "upstream_event_id"}
    if not isinstance(event, dict) or not required <= event.keys() or event.keys() - required - optional:
        raise InvalidEvent("INVALID_REQUEST")
    kind = event["type"]
    if kind not in ("message_new", "message_event", "message_allow", "message_deny"):
        raise InvalidEvent("UNSUPPORTED_EVENT")
    if any(type(event[key]) is not int or event[key] <= 0
           for key in ("group_id", "actor_subject", "peer_id")):
        raise InvalidEvent("INVALID_REQUEST")
    if tuple(event[key] for key in ("group_id", "actor_subject", "peer_id")) != trusted:
        raise InvalidEvent("SCOPE_DENIED")
    if kind == "message_new" and event["peer_id"] != event["actor_subject"]:
        raise InvalidEvent("SCOPE_DENIED")
    if not isinstance(event["api_version"], str) or not event["api_version"].strip():
        raise InvalidEvent("INVALID_REQUEST")
    stamp = event["occurred_at"]
    try:
        if not isinstance(stamp, str) or not re.fullmatch(
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z", stamp
        ):
            raise ValueError()
        datetime.fromisoformat(stamp)
    except ValueError as exc:
        raise InvalidEvent("INVALID_REQUEST") from exc
    command = event["command"]
    fields = {
        "menu_open": set(),
        "profile_submit": {"first_name", "last_name", "grade"},
        "parent_candidate": {"child_subject", "first_name", "last_name", "grade"},
        "confirm_booking": {"handle", "operation_id", "expected_revision"},
        "permission_changed": {"allowed"},
    }
    if not isinstance(command, dict) or not isinstance(command.get("action"), str):
        raise InvalidEvent("INVALID_REQUEST")
    action = command["action"]
    if action not in fields or command.keys() != fields[action] | {"action"}:
        raise InvalidEvent("INVALID_REQUEST")
    for key in ("first_name", "last_name"):
        if key in command:
            value = command[key]
            if not isinstance(value, str) or not 1 <= len(value.strip()) <= 100:
                raise InvalidEvent("INVALID_REQUEST")
            command[key] = value.strip()
    if "grade" in command and command["grade"] is not None:
        if type(command["grade"]) is not int or not 1 <= command["grade"] <= 11:
            raise InvalidEvent("INVALID_REQUEST")
    for key in ("child_subject", "handle"):
        if key in command and (not isinstance(command[key], str) or not command[key].strip()):
            raise InvalidEvent("INVALID_REQUEST")
    if action == "confirm_booking":
        try:
            UUID(command["operation_id"])
        except (ValueError, TypeError, AttributeError) as exc:
            raise InvalidEvent("INVALID_REQUEST") from exc
        if type(command["expected_revision"]) is not int or command["expected_revision"] < 1:
            raise InvalidEvent("INVALID_REQUEST")
    if kind in ("message_allow", "message_deny"):
        if action != "permission_changed" or type(command["allowed"]) is not bool:
            raise InvalidEvent("INVALID_REQUEST")
        if command["allowed"] != (kind == "message_allow"):
            raise InvalidEvent("INVALID_REQUEST")
    elif action == "permission_changed":
        raise InvalidEvent("INVALID_REQUEST")
    upstream = event.get("upstream_event_id")
    if "conversation_message_id" in event and (
        type(event["conversation_message_id"]) is not int or event["conversation_message_id"] <= 0
    ):
        raise InvalidEvent("EVENT_KEY_UNAVAILABLE")
    if upstream is not None:
        if not isinstance(upstream, str) or not 1 <= len(upstream) <= 200 or not upstream.strip():
            raise InvalidEvent("EVENT_KEY_UNAVAILABLE")
        key = [kind, "upstream", upstream]
    elif kind == "message_new" and type(event.get("conversation_message_id")) is int and event["conversation_message_id"] > 0:
        key = [kind, "conversation", event["peer_id"], event["conversation_message_id"]]
    else:
        raise InvalidEvent("EVENT_KEY_UNAVAILABLE")
    # One connection per offline harness. Group remains part of the local key.
    event["event_key"] = hashlib.sha256(canonical({"group": event["group_id"], "key": key}).encode()).hexdigest()
    return event
