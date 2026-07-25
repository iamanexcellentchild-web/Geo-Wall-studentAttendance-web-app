import hmac
import hashlib
import time
import math
from django.conf import settings


QR_TOKEN_TTL_SECONDS = 90  # matches PRD's rotating-QR expectation


def generate_qr_token(session_id: int, student_id: int) -> str:
    """Generate a signed, time-bound QR token for a student's check-in attempt."""
    issued_at = int(time.time())
    payload = f"{session_id}:{student_id}:{issued_at}"
    signature = hmac.new(
        settings.SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{payload}:{signature}"


def verify_qr_token(token: str):
    """
    Verify a QR token's signature and expiry.
    Returns (session_id, student_id) if valid, raises ValueError otherwise.
    """
    try:
        session_id, student_id, issued_at, signature = token.split(":")
    except ValueError:
        raise ValueError("Malformed token")

    payload = f"{session_id}:{student_id}:{issued_at}"
    expected_signature = hmac.new(
        settings.SECRET_KEY.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Invalid signature")

    if int(time.time()) - int(issued_at) > QR_TOKEN_TTL_SECONDS:
        raise ValueError("Token expired")

    return int(session_id), int(student_id)


def haversine_distance(lat1, lon1, lat2, lon2):
    """Returns distance in meters between two GPS coordinates."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)

    a = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c