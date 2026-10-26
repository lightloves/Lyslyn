"""Production-grade JSON Web Token (JWT) module for Lyslyn.

Zero-dependency standard RFC 7519 implementation using HMAC-SHA256 (HS256).
Supports payload signing, signature verification, expiration validation (exp),
not-before validation (nbf), and unverified inspection.
"""
import base64
import json
import time
import hmac
import hashlib
from typing import Any, Dict, Optional, Union
from ..values import LyslynBuiltin
from ..diagnostics import RuntimeError_


def _b64url_encode(data: bytes) -> str:
    """Encode bytes into URL-safe base64 without padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    """Decode URL-safe base64 string, restoring stripped padding."""
    s_bytes = s.encode("ascii")
    padding = 4 - (len(s_bytes) % 4)
    if padding < 4:
        s_bytes += b"=" * padding
    return base64.urlsafe_b64decode(s_bytes)


def jwt_sign(payload: Dict[str, Any], secret: str, expires_in: Optional[int] = 3600) -> str:
    """Sign a JWT token with HMAC-SHA256.

    Args:
        payload: Dictionary of claims to include.
        secret: Signing key.
        expires_in: Expiration time in seconds from now (default: 3600s / 1 hour). Pass 0 or nil for no expiry.
    """
    if not isinstance(payload, dict):
        raise RuntimeError_(f"JWT payload must be an object/dict, got {type(payload).__name__}")

    header = {"alg": "HS256", "typ": "JWT"}
    payload_copy = dict(payload)

    now = int(time.time())
    if "iat" not in payload_copy:
        payload_copy["iat"] = now

    if expires_in and expires_in > 0:
        payload_copy["exp"] = now + int(expires_in)

    header_json = json.dumps(header, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_json = json.dumps(payload_copy, separators=(",", ":"), sort_keys=True).encode("utf-8")

    header_b64 = _b64url_encode(header_json)
    payload_b64 = _b64url_encode(payload_json)

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(
        str(secret).encode("utf-8"),
        signing_input,
        hashlib.sha256
    ).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def jwt_verify(token: str, secret: str) -> Dict[str, Any]:
    """Verify a JWT signature and validate standard claims (exp, nbf).

    Returns decoded payload if valid, or raises an error.
    """
    token_str = str(token).strip()
    parts = token_str.split(".")
    if len(parts) != 3:
        raise RuntimeError_("Invalid JWT format: Token must contain exactly 3 dot-separated segments")

    header_b64, payload_b64, sig_b64 = parts

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    expected_sig = hmac.new(
        str(secret).encode("utf-8"),
        signing_input,
        hashlib.sha256
    ).digest()
    expected_sig_b64 = _b64url_encode(expected_sig)

    if not hmac.compare_digest(sig_b64, expected_sig_b64):
        raise RuntimeError_("JWT verification failed: Invalid signature")

    try:
        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        raise RuntimeError_(f"JWT error: Failed to decode payload JSON: {e}")

    now = int(time.time())
    if "exp" in payload and isinstance(payload["exp"], (int, float)):
        if now > payload["exp"]:
            raise RuntimeError_(f"JWT verification failed: Token expired at timestamp {payload['exp']} (current: {now})")

    if "nbf" in payload and isinstance(payload["nbf"], (int, float)):
        if now < payload["nbf"]:
            raise RuntimeError_(f"JWT verification failed: Token is not yet valid until {payload['nbf']}")

    return payload


def jwt_decode(token: str) -> Dict[str, Any]:
    """Decode a JWT payload without verifying its signature."""
    token_str = str(token).strip()
    parts = token_str.split(".")
    if len(parts) != 3:
        raise RuntimeError_("Invalid JWT format: Token must contain exactly 3 dot-separated segments")
    try:
        payload_bytes = _b64url_decode(parts[1])
        return json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        raise RuntimeError_(f"JWT error: Failed to decode payload: {e}")


def export_module() -> Dict[str, Any]:
    return {
        "sign": LyslynBuiltin("sign", jwt_sign),
        "verify": LyslynBuiltin("verify", jwt_verify, arity=2),
        "decode": LyslynBuiltin("decode", jwt_decode, arity=1),
    }
