"""Thread-safe, in-memory conversation state."""

from __future__ import annotations

import threading
from collections import OrderedDict

Message = dict[str, str]

_DEFAULT_DEDUPE_CAPACITY = 1000


class SessionStore:
    """Per-sender chat history, paused set, and message de-duplication."""

    def __init__(
        self,
        history_limit: int = 10,
        dedupe_capacity: int = _DEFAULT_DEDUPE_CAPACITY,
    ) -> None:
        if history_limit < 1:
            raise ValueError("history_limit must be >= 1")
        self._history_limit = history_limit
        self._dedupe_capacity = dedupe_capacity
        self._history: dict[str, list[Message]] = {}
        self._paused: set[str] = set()
        self._seen: OrderedDict[str, None] = OrderedDict()
        self._lock = threading.Lock()

    def _trim(self, history: list[Message]) -> None:
        excess = len(history) - self._history_limit
        if excess > 0:
            del history[:excess]

    def add_user_message(self, sender: str, text: str) -> list[Message]:
        """Append a user turn and return a snapshot of the trimmed history."""

        with self._lock:
            history = self._history.setdefault(sender, [])
            history.append({"role": "user", "text": text})
            self._trim(history)
            return [dict(item) for item in history]

    def add_model_message(self, sender: str, text: str) -> None:
        with self._lock:
            history = self._history.setdefault(sender, [])
            history.append({"role": "model", "text": text})
            self._trim(history)

    def get_history(self, sender: str) -> list[Message]:
        with self._lock:
            return [dict(item) for item in self._history.get(sender, [])]

    def clear_history(self, sender: str) -> None:
        with self._lock:
            self._history.pop(sender, None)

    def is_paused(self, sender: str) -> bool:
        with self._lock:
            return sender in self._paused

    def pause(self, sender: str) -> None:
        with self._lock:
            self._paused.add(sender)

    def resume(self, sender: str) -> None:
        with self._lock:
            self._paused.discard(sender)

    def paused_senders(self) -> set[str]:
        with self._lock:
            return set(self._paused)

    def mark_seen(self, message_id: str | None) -> bool:
        """Record ``message_id``; return True if it had already been seen."""

        if not message_id:
            return False
        with self._lock:
            if message_id in self._seen:
                self._seen.move_to_end(message_id)
                return True
            self._seen[message_id] = None
            while len(self._seen) > self._dedupe_capacity:
                self._seen.popitem(last=False)
            return False
