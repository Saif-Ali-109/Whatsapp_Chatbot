"""Human-handoff handling: pause/resume plus admin notifications and commands."""

from __future__ import annotations

import logging
import re

from .sessions import SessionStore
from .whatsapp import WhatsAppClient

logger = logging.getLogger(__name__)

_COMMAND_RE = re.compile(r"^(resume|pause|status)\b\s*(.*)$", re.IGNORECASE)


def normalize_number(value: str) -> str:
    """Reduce a human-typed number to digits only (WhatsApp wa_id form)."""

    return re.sub(r"\D", "", value or "")


class HandoffService:
    """Owns the bot's paused state and the admin command surface."""

    def __init__(
        self,
        sessions: SessionStore,
        whatsapp: WhatsAppClient,
        admin_number: str | None = None,
    ) -> None:
        self._sessions = sessions
        self._whatsapp = whatsapp
        self._admin_number = normalize_number(admin_number) if admin_number else None

    @property
    def admin_number(self) -> str | None:
        return self._admin_number

    def trigger_handoff(
        self, sender: str, history: list[dict[str, str]] | None = None
    ) -> None:
        """Pause the bot for ``sender`` and alert the admin if configured."""

        self._sessions.pause(sender)
        logger.info("Handoff requested; paused auto-replies for %s", sender)
        if not self._admin_number:
            return
        snippet = self._format_snippet(history or [])
        message = (
            f"Human handoff requested by {sender}.\n\n"
            f"{snippet}\n\n"
            f"Reply 'resume {sender}' to let the bot take over again."
        )
        self._whatsapp.send_text(self._admin_number, message)

    @staticmethod
    def _format_snippet(history: list[dict[str, str]], limit: int = 6) -> str:
        lines = []
        for turn in history[-limit:]:
            who = "Customer" if turn["role"] == "user" else "Bot"
            lines.append(f"{who}: {turn['text']}")
        return "\n".join(lines) if lines else "(no history)"

    def handle_admin_command(self, sender: str, text: str) -> bool:
        """Handle a command from the admin number.

        Returns True when the message was an admin command and should not be
        passed to the LLM.
        """

        if not self._admin_number or normalize_number(sender) != self._admin_number:
            return False
        match = _COMMAND_RE.match((text or "").strip())
        if not match:
            return False

        command = match.group(1).lower()
        target = normalize_number(match.group(2))

        if command == "resume":
            if not target:
                self._whatsapp.send_text(
                    sender, "Usage: resume <number> (digits with country code)."
                )
            else:
                self._sessions.resume(target)
                self._whatsapp.send_text(sender, f"Bot resumed for {target}.")
        elif command == "pause":
            if not target:
                self._whatsapp.send_text(
                    sender, "Usage: pause <number> (digits with country code)."
                )
            else:
                self._sessions.pause(target)
                self._whatsapp.send_text(sender, f"Bot paused for {target}.")
        else:  # status
            if not target:
                paused = ", ".join(sorted(self._sessions.paused_senders())) or "none"
                self._whatsapp.send_text(sender, f"Paused senders: {paused}.")
            else:
                state = "paused" if self._sessions.is_paused(target) else "active"
                self._whatsapp.send_text(sender, f"{target} is {state}.")

        return True
