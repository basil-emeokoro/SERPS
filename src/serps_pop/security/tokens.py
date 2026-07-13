from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from serps_pop.config.settings import get_settings

_DEV_SECRET = secrets.token_urlsafe(32)


class TokenError(ValueError):
    pass


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def _secret() -> str:
    settings = get_settings()
    configured = settings.jwt_secret.get_secret_value() if settings.jwt_secret else None
    if configured:
        return configured
    if settings.env.lower() not in {"development", "test", "local"}:
        raise TokenError("SERPS_JWT_SECRET must be configured outside development.")
    return _DEV_SECRET


def create_access_token(
    *,
    subject: str,
    institution_id: str,
    roles: list[str],
    expires_delta: timedelta | None = None,
) -> str:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    expires = now + (expires_delta or timedelta(minutes=settings.access_token_minutes))
    payload: dict[str, Any] = {
        "iss": settings.jwt_issuer,
        "sub": subject,
        "institution_id": institution_id,
        "roles": roles,
        "iat": int(now.timestamp()),
        "exp": int(expires.timestamp()),
        "typ": "access",
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = f"{_b64url(json.dumps(header, separators=(',', ':')).encode())}.{_b64url(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(_secret().encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        signing_input = f"{header_b64}.{payload_b64}"
        expected = hmac.new(_secret().encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
        actual = _b64url_decode(signature_b64)
        if not hmac.compare_digest(actual, expected):
            raise TokenError("Invalid token signature.")
        payload = json.loads(_b64url_decode(payload_b64))
        if payload.get("typ") != "access":
            raise TokenError("Invalid token type.")
        if payload.get("iss") != get_settings().jwt_issuer:
            raise TokenError("Invalid token issuer.")
        if int(payload.get("exp", 0)) < int(datetime.now(timezone.utc).timestamp()):
            raise TokenError("Token expired.")
        return payload
    except TokenError:
        raise
    except Exception as exc:
        raise TokenError("Invalid token.") from exc


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
