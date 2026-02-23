import hashlib
import random
import string
from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt

from app.core.config import settings

MOCK_VALID_OTP = "000000"


def hash_token(raw: str) -> str:
    """Return the SHA-256 hex digest of a raw token string.

    Only the hash is stored in the database; the raw token is returned to
    the client once and never persisted.  This means a DB leak does not
    expose usable tokens.
    """
    return hashlib.sha256(raw.encode()).hexdigest()


# ---------------------------------------------------------------------------
# OTP helpers
# ---------------------------------------------------------------------------


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP and print it to stdout (mock transport)."""
    otp = "".join(random.choices(string.digits, k=length))
    print(f"[MOCK OTP] Generated OTP: {otp}")
    return otp


def verify_otp(otp: str) -> bool:
    """Return True for the universal mock OTP or any generated OTP.

    In production this would validate against a short-lived cache / SMS provider.
    For now we always accept MOCK_VALID_OTP ('000000').
    """
    return otp == MOCK_VALID_OTP


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _utcnow() -> datetime:
    return datetime.now(UTC)


def create_access_token(subject: UUID | str, extra_claims: dict | None = None) -> str:
    """Create a short-lived JWT access token."""
    expire = _utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload: dict = {
        "sub": str(subject),
        "exp": expire,
        "iat": _utcnow(),
        "type": "access",
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.APP_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Raises:
        jose.JWTError: if the token is invalid or expired.
    """
    payload = jwt.decode(
        token,
        settings.APP_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    if payload.get("type") != "access":
        raise JWTError("Not an access token")
    return payload
