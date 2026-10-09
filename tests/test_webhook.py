import json

from app.signature import compute_signature
from app.webhook import handle_post, handle_verification


def make_payload(sender="15551112222", message_id="wamid.1", msg_type="text", text="hi"):
    message = {"from": sender, "id": message_id, "type": msg_type}
    if msg_type == "text":
        message["text"] = {"body": text}
    return {"entry": [{"changes": [{"value": {"messages": [message]}}]}]}


def post(services, payload, sign=True):
    raw = json.dumps(payload).encode()
    signature = compute_signature(services.config.app_secret, raw) if sign else "sha256=bad"
    return handle_post(services, raw, signature)


# --- GET verification -------------------------------------------------------


def test_get_verification_success(config):
    body, status = handle_verification(
        config,
        {"hub.mode": "subscribe", "hub.verify_token": "verify-me", "hub.challenge": "42"},
    )
    assert (body, status) == ("42", 200)


def test_get_verification_failure(config):
    body, status = handle_verification(
        config, {"hub.mode": "subscribe", "hub.verify_token": "nope"}
    )
    assert status == 403


# --- POST signature ---------------------------------------------------------


def test_post_rejects_invalid_signature(services):
    body, status = post(services, make_payload(), sign=False)
    assert status == 403
    assert services.whatsapp.texts == []
    assert services.sessions.get_history("15551112222") == []


def test_post_rejects_when_signature_missing(services):
    _, status = handle_post(services, b"{}", None)
    assert status == 403


def test_invalid_json_is_acked(services):
    raw = b"not-json"
    signature = compute_signature(services.config.app_secret, raw)
    body, status = handle_post(services, raw, signature)
    assert status == 200
    assert body == {"status": "received"}


# --- Text handling ----------------------------------------------------------


def test_text_message_gets_reply(services):
    body, status = post(services, make_payload(text="hello"))

    assert status == 200
    assert body == {"status": "received"}
    assert services.whatsapp.reads == ["wamid.1"]
    assert services.whatsapp.texts == [("15551112222", "Hello!")]
    assert services.sessions.get_history("15551112222") == [
        {"role": "user", "text": "hello"},
        {"role": "model", "text": "Hello!"},
    ]
    assert services.llm.calls[-1][-1] == {"role": "user", "text": "hello"}


def test_duplicate_message_is_ignored(services):
    payload = make_payload(message_id="dup")
    post(services, payload)
    post(services, payload)

    assert len(services.whatsapp.texts) == 1
    assert len(services.llm.calls) == 1


def test_multiple_messages_in_one_payload(services):
    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {"from": "1", "id": "a", "type": "text", "text": {"body": "one"}},
                                {"from": "2", "id": "b", "type": "text", "text": {"body": "two"}},
                            ]
                        }
                    }
                ]
            }
        ]
    }
    post(services, payload)
    assert ("1", "Hello!") in services.whatsapp.texts
    assert ("2", "Hello!") in services.whatsapp.texts


# --- Non-text ---------------------------------------------------------------


def test_non_text_message_gets_notice(services):
    post(services, make_payload(message_id="img", msg_type="image"))

    assert services.whatsapp.texts == [
        ("15551112222", services.config.non_text_notice)
    ]
    assert services.llm.calls == []


# --- Paused senders ---------------------------------------------------------


def test_paused_sender_is_not_replied_to(services):
    services.sessions.pause("15551112222")
    post(services, make_payload(text="anyone there?"))

    assert services.whatsapp.texts == []
    assert services.llm.calls == []


# --- Admin commands ---------------------------------------------------------


def test_admin_resume_command(services):
    admin = services.config.admin_whatsapp_number
    services.sessions.pause("15551112222")

    post(
        services,
        make_payload(sender=admin, message_id="cmd1", text="resume 15551112222"),
    )

    assert services.sessions.is_paused("15551112222") is False
    assert services.llm.calls == []
    assert any(to == admin for to, _ in services.whatsapp.texts)


def test_non_admin_cannot_resume(services):
    services.sessions.pause("15551112222")
    post(
        services,
        make_payload(sender="19998887777", message_id="cmd2", text="resume 15551112222"),
    )
    assert services.sessions.is_paused("15551112222") is True


# --- Failure & handoff ------------------------------------------------------


def test_llm_failure_sends_fallback(services):
    class BoomLLM:
        def generate_reply(self, history):
            raise RuntimeError("gemini down")

    services.llm = BoomLLM()
    post(services, make_payload())

    assert services.whatsapp.texts == [
        ("15551112222", services.config.fallback_message)
    ]


def test_handoff_pauses_sender_and_notifies_admin(services):
    class HandoffLLM:
        def generate_reply(self, history):
            return "Connecting you with a team member.", True

    services.llm = HandoffLLM()
    post(services, make_payload())

    admin = services.config.admin_whatsapp_number
    assert services.sessions.is_paused("15551112222") is True
    assert ("15551112222", "Connecting you with a team member.") in services.whatsapp.texts
    assert any(to == admin for to, _ in services.whatsapp.texts)
