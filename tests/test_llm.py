from app.llm import LLMClient


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self, response):
        self._response = response
        self.last_kwargs = None

    def generate_content(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class FakeGenaiClient:
    def __init__(self, response):
        self.models = FakeModels(response)


def make_client(response_text, **kwargs):
    fake = FakeGenaiClient(FakeResponse(response_text))
    client = LLMClient(
        api_key="unused",
        model="gemini-3.5-flash-lite",
        system_prompt="be nice",
        client=fake,
        **kwargs,
    )
    return client, fake


def test_generate_reply_returns_text_without_marker():
    client, _ = make_client("All good!")
    text, handoff = client.generate_reply([{"role": "user", "text": "hi"}])
    assert text == "All good!"
    assert handoff is False


def test_generate_reply_strips_handoff_marker():
    client, _ = make_client("Connecting you now. <<HANDOFF>>")
    text, handoff = client.generate_reply([{"role": "user", "text": "human please"}])
    assert handoff is True
    assert text == "Connecting you now."
    assert "<<HANDOFF>>" not in text


def test_generate_reply_handles_empty_output():
    client, _ = make_client(None)
    text, handoff = client.generate_reply([{"role": "user", "text": "hi"}])
    assert text == ""
    assert handoff is False


def test_history_is_mapped_to_gemini_contents():
    client, fake = make_client("ok")
    history = [
        {"role": "user", "text": "first"},
        {"role": "model", "text": "reply"},
        {"role": "user", "text": "second"},
    ]
    client.generate_reply(history)

    contents = fake.models.last_kwargs["contents"]
    assert [item.role for item in contents] == ["user", "model", "user"]
    assert [item.parts[0].text for item in contents] == ["first", "reply", "second"]


def test_system_prompt_is_passed():
    client, fake = make_client("ok")
    client.generate_reply([{"role": "user", "text": "hi"}])
    config = fake.models.last_kwargs["config"]
    assert config.system_instruction == "be nice"
    assert fake.models.last_kwargs["model"] == "gemini-3.5-flash-lite"
