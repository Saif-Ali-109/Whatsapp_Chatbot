"""Gemini-backed reply generation."""

from __future__ import annotations

import logging

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class LLMClient:
    """Generates a support reply from a conversation history."""

    def __init__(
        self,
        api_key: str,
        model: str,
        system_prompt: str,
        handoff_marker: str = "<<HANDOFF>>",
        client: object | None = None,
    ) -> None:
        self._model = model
        self._system_prompt = system_prompt
        self._handoff_marker = handoff_marker
        # ``client`` is injectable so tests never touch the network.
        self._client = client or genai.Client(api_key=api_key)

    def _build_config(self) -> types.GenerateContentConfig:
        kwargs: dict = {"system_instruction": self._system_prompt}
        # 3.5 Flash-Lite supports a "minimal" thinking level for low latency.
        # Guard against SDK versions that do not expose it yet.
        try:
            kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_level=types.ThinkingLevel.MINIMAL
            )
        except Exception:  # pragma: no cover - defensive for older SDKs
            pass
        return types.GenerateContentConfig(**kwargs)

    @staticmethod
    def _to_contents(history: list[dict[str, str]]) -> list[types.Content]:
        return [
            types.Content(
                role=turn["role"],
                parts=[types.Part.from_text(text=turn["text"])],
            )
            for turn in history
        ]

    def generate_reply(self, history: list[dict[str, str]]) -> tuple[str, bool]:
        """Return ``(reply_text, handoff_requested)`` for the given history."""

        response = self._client.models.generate_content(
            model=self._model,
            contents=self._to_contents(history),
            config=self._build_config(),
        )
        text = (getattr(response, "text", None) or "").strip()
        handoff = self._handoff_marker in text
        if handoff:
            text = text.replace(self._handoff_marker, "").strip()
        return text, handoff
