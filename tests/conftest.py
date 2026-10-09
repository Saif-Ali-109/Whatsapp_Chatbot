"""Shared pytest fixtures and fakes."""

from __future__ import annotations

import pytest

from app.config import Config
from app.context import Services
from app.handoff import HandoffService
from app.sessions import SessionStore


class FakeWhatsApp:
    def __init__(self) -> None:
        self.texts: list[tuple[str, str]] = []
        self.reads: list[str] = []

    def send_text(self, to: str, text: str) -> None:
        self.texts.append((to, text))

    def mark_read_with_typing(self, message_id: str) -> None:
        self.reads.append(message_id)


class FakeLLM:
    def __init__(self, reply: str = "Hello!", handoff: bool = False) -> None:
        self.reply = reply
        self.handoff = handoff
        self.calls: list[list[dict[str, str]]] = []

    def generate_reply(self, history):
        self.calls.append([dict(turn) for turn in history])
        return self.reply, self.handoff


class FakeExecutor:
    """Runs submitted work synchronously so tests are deterministic."""

    def submit(self, fn, *args, **kwargs):
        return fn(*args, **kwargs)


@pytest.fixture
def config() -> Config:
    return Config(
        access_token="token",
        phone_number_id="12345",
        verify_token="verify-me",
        gemini_api_key="gemini-key",
        app_secret="app-secret",
        admin_whatsapp_number="15550000000",
        validate_signature=True,
        history_limit=10,
    )


@pytest.fixture
def whatsapp() -> FakeWhatsApp:
    return FakeWhatsApp()


@pytest.fixture
def sessions() -> SessionStore:
    return SessionStore(history_limit=10)


@pytest.fixture
def services(config, whatsapp, sessions) -> Services:
    handoff = HandoffService(sessions, whatsapp, config.admin_whatsapp_number)
    return Services(
        config=config,
        whatsapp=whatsapp,
        llm=FakeLLM(),
        sessions=sessions,
        handoff=handoff,
        executor=FakeExecutor(),
    )
