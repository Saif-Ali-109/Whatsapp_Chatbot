import pytest

from app.sessions import SessionStore


def test_history_is_trimmed_to_limit():
    store = SessionStore(history_limit=4)
    for i in range(6):
        store.add_user_message("user", f"m{i}")

    history = store.get_history("user")
    assert [turn["text"] for turn in history] == ["m2", "m3", "m4", "m5"]


def test_add_user_message_returns_snapshot():
    store = SessionStore(history_limit=4)
    snapshot = store.add_user_message("user", "hello")
    snapshot.append({"role": "user", "text": "injected"})

    assert store.get_history("user") == [{"role": "user", "text": "hello"}]


def test_roles_are_preserved():
    store = SessionStore(history_limit=4)
    store.add_user_message("user", "hi")
    store.add_model_message("user", "hello")

    assert store.get_history("user") == [
        {"role": "user", "text": "hi"},
        {"role": "model", "text": "hello"},
    ]


def test_history_limit_must_be_positive():
    with pytest.raises(ValueError):
        SessionStore(history_limit=0)


def test_pause_and_resume():
    store = SessionStore()
    assert store.is_paused("user") is False
    store.pause("user")
    assert store.is_paused("user") is True
    assert store.paused_senders() == {"user"}
    store.resume("user")
    assert store.is_paused("user") is False


def test_mark_seen_detects_duplicates():
    store = SessionStore()
    assert store.mark_seen("wamid.1") is False
    assert store.mark_seen("wamid.1") is True
    assert store.mark_seen(None) is False


def test_mark_seen_evicts_oldest():
    store = SessionStore(dedupe_capacity=2)
    store.mark_seen("a")
    store.mark_seen("b")
    store.mark_seen("c")  # evicts "a"

    assert store.mark_seen("a") is False
    assert store.mark_seen("c") is True
