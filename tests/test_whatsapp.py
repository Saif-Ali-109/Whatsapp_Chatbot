from app.whatsapp import WHATSAPP_TEXT_LIMIT, WhatsAppClient, split_message


def test_split_short_message_is_single_chunk():
    assert split_message("hello") == ["hello"]


def test_split_empty_message_returns_no_chunks():
    assert split_message("") == []


def test_split_prefers_newline_boundaries():
    text = "a" * 10 + "\n" + "b" * 10
    chunks = split_message(text, limit=12)
    assert all(len(chunk) <= 12 for chunk in chunks)
    assert chunks[0] == "a" * 10
    assert chunks[1] == "b" * 10


def test_split_word_boundaries_and_limit():
    text = " ".join(f"word{i}" for i in range(500))
    chunks = split_message(text, limit=100)
    assert len(chunks) > 1
    assert all(0 < len(chunk) <= 100 for chunk in chunks)
    # No word is broken in half (aside from the hard-split fallback).
    for chunk in chunks:
        assert "  " not in chunk


def test_split_hard_cuts_unbroken_strings():
    text = "x" * 250
    chunks = split_message(text, limit=100)
    assert [len(c) for c in chunks] == [100, 100, 50]


def test_split_handles_default_limit():
    text = "a" * (WHATSAPP_TEXT_LIMIT + 1)
    chunks = split_message(text)
    assert sum(len(c) for c in chunks) == WHATSAPP_TEXT_LIMIT + 1


class FakeResponse:
    ok = True
    status_code = 200
    text = ""

    def json(self):
        return {"messages": [{"id": "wamid.1"}]}


def test_send_text_splits_and_posts_each_chunk(monkeypatch):
    posts = []

    def fake_post(url, headers=None, json=None, timeout=None):
        posts.append({"url": url, "headers": headers, "json": json})
        return FakeResponse()

    monkeypatch.setattr("app.whatsapp.requests.post", fake_post)

    client = WhatsAppClient("token", "12345", "v24.0")
    long_text = " ".join(["word"] * 3000)
    client.send_text("15551112222", long_text)

    assert len(posts) == len(split_message(long_text))
    for post in posts:
        assert post["json"]["to"] == "15551112222"
        assert post["json"]["type"] == "text"
        assert len(post["json"]["text"]["body"]) <= WHATSAPP_TEXT_LIMIT
        assert post["headers"]["Authorization"] == "Bearer token"
        assert post["url"].endswith("/12345/messages")


def test_mark_read_with_typing_payload(monkeypatch):
    captured = {}

    def fake_post(url, headers=None, json=None, timeout=None):
        captured.update(json)
        return FakeResponse()

    monkeypatch.setattr("app.whatsapp.requests.post", fake_post)

    WhatsAppClient("token", "12345").mark_read_with_typing("wamid.abc")

    assert captured["status"] == "read"
    assert captured["message_id"] == "wamid.abc"
    assert captured["typing_indicator"] == {"type": "text"}
    assert captured["messaging_product"] == "whatsapp"
