"""Flask blueprint implementing the WhatsApp webhook."""

from __future__ import annotations

import json
import logging
from typing import Any

from flask import Blueprint, jsonify, request

from .context import Services
from .signature import verify_signature

logger = logging.getLogger(__name__)


def handle_verification(config: Any, args: Any) -> tuple[str, int]:
    """Validate Meta's GET handshake and echo the challenge."""

    if (
        args.get("hub.mode") == "subscribe"
        and args.get("hub.verify_token") == config.verify_token
    ):
        return args.get("hub.challenge", ""), 200
    return "Invalid verification token", 403


def parse_messages(payload: dict) -> list[dict]:
    """Flatten all inbound messages across entries/changes in one payload."""

    messages: list[dict] = []
    for entry in payload.get("entry", []) or []:
        for change in entry.get("changes", []) or []:
            value = change.get("value", {}) or {}
            messages.extend(value.get("messages", []) or [])
    return messages


def dispatch_message(services: Services, message: dict) -> None:
    """Route a single inbound message."""

    sender = message.get("from")
    if not sender:
        return

    message_id = message.get("id")
    if services.sessions.mark_seen(message_id):
        logger.info("Ignoring duplicate message %s", message_id)
        return

    msg_type = message.get("type")
    text = (message.get("text") or {}).get("body", "") if msg_type == "text" else ""

    if services.handoff.handle_admin_command(sender, text):
        return

    if services.sessions.is_paused(sender):
        logger.info("Sender %s is paused; not auto-replying.", sender)
        return

    if msg_type != "text":
        services.whatsapp.send_text(sender, services.config.non_text_notice)
        return

    if message_id:
        try:
            services.whatsapp.mark_read_with_typing(message_id)
        except Exception:  # pragma: no cover - best effort UX
            logger.exception("Failed to show typing indicator for %s", sender)

    history = services.sessions.add_user_message(sender, text)
    services.executor.submit(process_reply, services, sender, history)


def process_reply(
    services: Services, sender: str, history: list[dict[str, str]]
) -> None:
    """Generate and send a reply (runs in the background)."""

    try:
        reply, handoff = services.llm.generate_reply(history)
    except Exception:
        logger.exception("LLM generation failed for %s", sender)
        services.whatsapp.send_text(sender, services.config.fallback_message)
        return

    if not reply:
        reply = services.config.fallback_message

    services.sessions.add_model_message(sender, reply)
    services.whatsapp.send_text(sender, reply)

    if handoff:
        services.handoff.trigger_handoff(sender, services.sessions.get_history(sender))


def handle_post(services: Services, raw_body: bytes, signature: str | None) -> tuple[Any, int]:
    """Verify, parse, and dispatch an inbound webhook POST."""

    if services.config.validate_signature and not verify_signature(
        services.config.app_secret, raw_body, signature
    ):
        logger.warning("Rejected webhook POST with invalid signature")
        return "Invalid signature", 403

    try:
        payload = json.loads(raw_body or b"{}")
    except (ValueError, TypeError):
        logger.exception("Could not parse webhook payload")
        return {"status": "received"}, 200

    if isinstance(payload, dict):
        for message in parse_messages(payload):
            try:
                dispatch_message(services, message)
            except Exception:  # pragma: no cover - never fail the webhook
                logger.exception("Error dispatching message")

    return {"status": "received"}, 200


def build_blueprint(services: Services) -> Blueprint:
    bp = Blueprint("whatsapp", __name__)

    @bp.route("/whatsapp-webhook", methods=["GET", "POST"])
    def whatsapp_webhook():  # pragma: no cover - exercised via helper functions
        if request.method == "GET":
            body, status = handle_verification(services.config, request.args)
            return body, status
        body, status = handle_post(
            services, request.get_data(), request.headers.get("X-Hub-Signature-256")
        )
        return (jsonify(body) if isinstance(body, dict) else body), status

    return bp
