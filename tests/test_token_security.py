from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import timedelta

import pytest

from serps_pop.security.tokens import TokenError, create_access_token, decode_access_token


def encode(value: dict) -> str:
    return base64.urlsafe_b64encode(json.dumps(value, separators=(",", ":")).encode()).rstrip(b"=").decode()


def decode(value: str) -> dict:
    return json.loads(base64.urlsafe_b64decode(value + "=" * (-len(value) % 4)))


def resign(token: str, **claim_changes: object) -> str:
    header_b64, payload_b64, _ = token.split(".")
    payload = decode(payload_b64)
    payload.update(claim_changes)
    payload_b64 = encode(payload)
    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(
        os.environ["SERPS_JWT_SECRET"].encode(), signing_input.encode(), hashlib.sha256
    ).digest()
    signature_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode()
    return f"{signing_input}.{signature_b64}"


def valid_token(**overrides: object) -> str:
    values = {"subject": "USER-1", "institution_id": "INST-1", "roles": ["Candidate"]}
    values.update(overrides)
    return create_access_token(**values)


def test_valid_token_contains_and_validates_required_scope():
    payload = decode_access_token(valid_token())

    assert payload["aud"] == "serps-api"
    assert payload["institution_id"] == "INST-1"
    assert payload["roles"] == ["Candidate"]


def test_expired_token_is_rejected():
    with pytest.raises(TokenError, match="expired"):
        decode_access_token(valid_token(expires_delta=timedelta(seconds=-1)))


def test_invalid_signature_is_rejected():
    token = valid_token()
    replacement = "A" if token[-1] != "A" else "B"

    with pytest.raises(TokenError, match="signature"):
        decode_access_token(token[:-1] + replacement)


@pytest.mark.parametrize(
    "changes,message",
    [
        ({"iss": "wrong-issuer"}, "issuer"),
        ({"aud": "wrong-audience"}, "audience"),
        ({"roles": []}, "roles"),
        ({"institution_id": ""}, "institution"),
    ],
)
def test_incorrect_or_missing_scope_is_rejected(changes: dict, message: str):
    with pytest.raises(TokenError, match=message):
        decode_access_token(resign(valid_token(), **changes))


def test_malformed_token_is_rejected():
    with pytest.raises(TokenError, match="Invalid token"):
        decode_access_token("not-a-jwt")
