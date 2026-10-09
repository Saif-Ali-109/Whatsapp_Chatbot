"""Application factory and dependency wiring."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor

from flask import Flask

from .config import Config, load_config
from .context import Services
from .handoff import HandoffService
from .llm import LLMClient
from .sessions import SessionStore
from .webhook import build_blueprint
from .whatsapp import WhatsAppClient

logger = logging.getLogger(__name__)


def build_services(
    config: Config,
    *,
    whatsapp: object | None = None,
    llm: object | None = None,
    sessions: SessionStore | None = None,
    handoff: HandoffService | None = None,
    executor: object | None = None,
    max_workers: int = 4,
) -> Services:
    """Construct the collaborator bundle, allowing test overrides."""

    whatsapp = whatsapp or WhatsAppClient(
        config.access_token, config.phone_number_id, config.graph_api_version
    )
    sessions = sessions or SessionStore(config.history_limit)
    llm = llm or LLMClient(
        config.gemini_api_key,
        config.gemini_model,
        config.system_prompt,
        config.handoff_marker,
    )
    handoff = handoff or HandoffService(sessions, whatsapp, config.admin_whatsapp_number)
    executor = executor or ThreadPoolExecutor(max_workers=max_workers)
    return Services(
        config=config,
        whatsapp=whatsapp,
        llm=llm,
        sessions=sessions,
        handoff=handoff,
        executor=executor,
    )


def create_app(config: Config | None = None, **overrides: object) -> Flask:
    """Create the Flask app, wiring real services unless overridden."""

    config = config or load_config()
    services = build_services(config, **overrides)
    app = Flask(__name__)
    app.register_blueprint(build_blueprint(services))
    logger.info("WhatsApp chatbot ready (model=%s)", config.gemini_model)
    return app
