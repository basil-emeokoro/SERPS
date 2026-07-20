from __future__ import annotations

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from serps_pop.config.settings import get_settings

class TokenError(ValueError):
    pass


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def _secret() -> str:
    configured = get_settings().jwt_secret.get_secret_value()
    if len(configured) < 32:
        raise TokenError("SERPS_JWT_SECRET must contain at least 32 characters.")
    return configured


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
        "aud": settings.jwt_audience,
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
        header = json.loads(_b64url_decode(header_b64))
        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise TokenError("Invalid token header.")
        signing_input = f"{header_b64}.{payload_b64}"
        expected = hmac.new(_secret().encode("utf-8"), signing_input.encode("ascii"), hashlib.sha256).digest()
        actual = _b64url_decode(signature_b64)
        if not hmac.compare_digest(actual, expected):
            raise TokenError("Invalid token signature.")
        payload = json.loads(_b64url_decode(payload_b64))
        required = {"iss", "aud", "sub", "institution_id", "roles", "iat", "exp", "typ"}
        if not required.issubset(payload):
            raise TokenError("Token is missing required claims.")
        if payload.get("typ") != "access":
            raise TokenError("Invalid token type.")
        settings = get_settings()
        if payload.get("iss") != settings.jwt_issuer:
            raise TokenError("Invalid token issuer.")
        if payload.get("aud") != settings.jwt_audience:
            raise TokenError("Invalid token audience.")
        if not isinstance(payload.get("sub"), str) or not payload["sub"]:
            raise TokenError("Invalid token subject.")
        if not isinstance(payload.get("institution_id"), str) or not payload["institution_id"]:
            raise TokenError("Invalid token institution.")
        roles = payload.get("roles")
        if not isinstance(roles, list) or not roles or not all(isinstance(role, str) and role for role in roles):
            raise TokenError("Invalid token roles.")
        now = int(datetime.now(timezone.utc).timestamp())
        if int(payload.get("exp", 0)) <= now:
            raise TokenError("Token expired.")
        if int(payload.get("iat", 0)) > now + 60:
            raise TokenError("Token issued-at time is invalid.")
        return payload
    except TokenError:
        raise
    except Exception as exc:
        raise TokenError("Invalid token.") from exc


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
