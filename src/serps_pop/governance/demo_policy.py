"""Process-local controls for an explicitly enabled prototype demonstration only.

This is deliberately not a production security control. State is session-scoped,
defaults to disarmed, and is lost when the API process restarts.
"""

from datetime import datetime, timezone
from threading import Lock

_armed_sessions: dict[str, datetime] = {}
_lock = Lock()


def phone_protection_is_armed(session_id: str) -> bool:
    with _lock:
        return session_id in _armed_sessions


def phone_protection_armed_at(session_id: str) -> datetime | None:
    with _lock:
        return _armed_sessions.get(session_id)


def set_phone_protection_armed(session_id: str, armed: bool) -> None:
    with _lock:
        if armed:
            _armed_sessions[session_id] = datetime.now(timezone.utc)
        else:
            _armed_sessions.pop(session_id, None)
