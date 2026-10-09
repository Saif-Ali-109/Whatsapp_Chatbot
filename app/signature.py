"""HMAC-SHA256 verification for Meta webhook payloads."""

from __future__ import annotations

import hashlib
import hmac

_PREFIX = "sha256="


def compute_signature(app_secret: str, raw_body: bytes) -> str:
    """Return the ``sha256=<hex>`` signature Meta would send for ``raw_body``."""

    digest = hmac.new(app_secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return f"{_PREFIX}{digest}"


def verify_signature(
    app_secret: str, raw_body: bytes, signature_header: str | None
) -> bool:
    """Constant-time comparison of the header against the expected digest."""

    if not app_secret or not signature_header:
        return False
    if not signature_header.startswith(_PREFIX):
        return False
    expected = compute_signature(app_secret, raw_body)
    return hmac.compare_digest(expected, signature_header)
