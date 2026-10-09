"""Environment-backed configuration for the WhatsApp chatbot."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

load_dotenv()

DEFAULT_HANDOFF_MARKER = "<<HANDOFF>>"

DEFAULT_SYSTEM_PROMPT = (
    "You are a friendly, professional customer support assistant for our business, "
    "replying to customers on WhatsApp.\n"
    "Guidelines:\n"
    "- Be concise and warm. Use short paragraphs suitable for a chat.\n"
    "- Answer questions about our products and services helpfully and accurately.\n"
    "- Never invent prices, policies, order status, or other facts you do not know. "
    "If you are unsure, say so honestly and offer to help further.\n"
    "- Reply in the same language the customer used.\n"
    "- Write plain text only: do not use Markdown such as **, #, or bullet symbols.\n"
    "- Keep replies under about 1000 characters whenever possible.\n"
    f"- If the customer explicitly asks for a human, is clearly frustrated, or the "
    f"request cannot be resolved, write a short message saying you will connect them "
    f"with a team member, and append the exact token {DEFAULT_HANDOFF_MARKER} at the "
    f"very end of your reply.\n"
)

DEFAULT_FALLBACK_MESSAGE = (
    "Sorry, I'm having trouble responding right now. Please try again in a moment."
)

DEFAULT_NON_TEXT_NOTICE = (
    "Sorry, I can only read text messages at the moment. "
    "Could you type out your question instead?"
)


def _get_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    """Fully resolved runtime configuration."""

    access_token: str
    phone_number_id: str
    verify_token: str
    gemini_api_key: str
    app_secret: str = ""
    admin_whatsapp_number: str | None = None
    gemini_model: str = "gemini-3.5-flash-lite"
    history_limit: int = 10
    graph_api_version: str = "v24.0"
    system_prompt: str = DEFAULT_SYSTEM_PROMPT
    fallback_message: str = DEFAULT_FALLBACK_MESSAGE
    non_text_notice: str = DEFAULT_NON_TEXT_NOTICE
    validate_signature: bool = True
    port: int = 5000
    handoff_marker: str = field(default=DEFAULT_HANDOFF_MARKER, repr=False)


def load_config() -> Config:
    """Read configuration from the environment, failing fast when incomplete."""

    required = {
        "ACCESS_TOKEN": os.getenv("ACCESS_TOKEN"),
        "PHONE_NUMBER_ID": os.getenv("PHONE_NUMBER_ID"),
        "VERIFY_TOKEN": os.getenv("VERIFY_TOKEN"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY"),
    }
    validate_signature = _get_bool("VALIDATE_SIGNATURE", True)
    if validate_signature:
        required["APP_SECRET"] = os.getenv("APP_SECRET")

    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: "
            + ", ".join(sorted(missing))
            + ". See .env.example."
        )

    admin = os.getenv("ADMIN_WHATSAPP_NUMBER") or None

    return Config(
        access_token=required["ACCESS_TOKEN"] or "",
        phone_number_id=required["PHONE_NUMBER_ID"] or "",
        verify_token=required["VERIFY_TOKEN"] or "",
        gemini_api_key=required["GEMINI_API_KEY"] or "",
        app_secret=required.get("APP_SECRET") or "",
        admin_whatsapp_number=admin,
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        history_limit=int(os.getenv("HISTORY_LIMIT", "10")),
        graph_api_version=os.getenv("GRAPH_API_VERSION", "v24.0"),
        system_prompt=os.getenv("SYSTEM_PROMPT") or DEFAULT_SYSTEM_PROMPT,
        fallback_message=os.getenv("FALLBACK_MESSAGE") or DEFAULT_FALLBACK_MESSAGE,
        non_text_notice=os.getenv("NON_TEXT_NOTICE") or DEFAULT_NON_TEXT_NOTICE,
        validate_signature=validate_signature,
        port=int(os.getenv("PORT", "5000")),
    )
