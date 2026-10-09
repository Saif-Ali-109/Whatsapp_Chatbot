"""Shared runtime dependencies for the webhook layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .config import Config


class Executor(Protocol):
    def submit(self, fn: Any, *args: Any, **kwargs: Any) -> Any: ...


@dataclass
class Services:
    """Bundle of collaborators passed to the webhook handlers."""

    config: Config
    whatsapp: Any
    llm: Any
    sessions: Any
    handoff: Any
    executor: Executor
