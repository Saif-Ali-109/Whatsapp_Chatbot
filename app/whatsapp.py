"""WhatsApp Cloud API client and message-splitting helpers."""

from __future__ import annotations

import logging

import requests

logger = logging.getLogger(__name__)

WHATSAPP_TEXT_LIMIT = 4096
DEFAULT_TIMEOUT = 10


def split_message(text: str, limit: int = WHATSAPP_TEXT_LIMIT) -> list[str]:
    """Split ``text`` into chunks of at most ``limit`` characters.

    Splitting prefers newline boundaries, then spaces, and finally falls back to a
    hard cut for long unbroken strings. Whitespace at chunk boundaries is trimmed.
    """

    if not text:
        return []
    if len(text) <= limit:
        return [text]

    chunks: list[str] = []
    remaining = text
    while len(remaining) > limit:
        window = remaining[:limit]
        split_at = window.rfind("\n")
        if split_at <= 0:
            split_at = window.rfind(" ")
        if split_at <= 0:
            split_at = limit
        chunk = remaining[:split_at].rstrip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_at:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks


class WhatsAppClient:
    """Thin wrapper over the Graph API ``messages`` endpoint."""

    def __init__(
        self,
        access_token: str,
        phone_number_id: str,
        api_version: str = "v24.0",
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        self._access_token = access_token
        self._phone_number_id = phone_number_id
        self._api_version = api_version
        self._timeout = timeout

    @property
    def _url(self) -> str:
        return (
            f"https://graph.facebook.com/{self._api_version}/"
            f"{self._phone_number_id}/messages"
        )

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    def _post(self, payload: dict) -> dict:
        response = requests.post(
            self._url, headers=self._headers, json=payload, timeout=self._timeout
        )
        try:
            body = response.json()
        except ValueError:
            body = {"raw": response.text}
        if not response.ok:
            logger.error("WhatsApp API error %s: %s", response.status_code, body)
        return body

    def send_text(self, to: str, text: str) -> None:
        """Send ``text`` (splitting into multiple messages when necessary)."""

        for chunk in split_message(text):
            self._post(
                {
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "text",
                    "text": {"body": chunk},
                }
            )

    def mark_read_with_typing(self, message_id: str) -> None:
        """Mark an inbound message as read and show the typing indicator."""

        self._post(
            {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id,
                "typing_indicator": {"type": "text"},
            }
        )
