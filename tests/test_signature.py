from app.signature import compute_signature, verify_signature

# Reference vector: HMAC-SHA256("Good morning", key="very_secret_key").
KNOWN_BODY = b"Good morning"
KNOWN_SECRET = "very_secret_key"
KNOWN_SIGNATURE = (
    "sha256=63e447ebe2bb46cb621972656087950c9d3a437caa61ece01f18094cc99f5a16"
)


def test_compute_signature_matches_known_vector():
    assert compute_signature(KNOWN_SECRET, KNOWN_BODY) == KNOWN_SIGNATURE


def test_verify_valid_signature():
    assert verify_signature(KNOWN_SECRET, KNOWN_BODY, KNOWN_SIGNATURE) is True


def test_verify_rejects_tampered_body():
    assert verify_signature(KNOWN_SECRET, b"Good evening", KNOWN_SIGNATURE) is False


def test_verify_rejects_wrong_secret():
    assert verify_signature("other-secret", KNOWN_BODY, KNOWN_SIGNATURE) is False


def test_verify_rejects_missing_or_malformed_header():
    assert verify_signature(KNOWN_SECRET, KNOWN_BODY, None) is False
    assert verify_signature(KNOWN_SECRET, KNOWN_BODY, "") is False
    assert verify_signature(KNOWN_SECRET, KNOWN_BODY, "deadbeef") is False


def test_verify_rejects_missing_secret():
    assert verify_signature("", KNOWN_BODY, KNOWN_SIGNATURE) is False
