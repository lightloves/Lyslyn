"""Production cryptography & security module for Lyslyn."""
import hashlib
import hmac
import secrets
import uuid
from typing import Any, Dict
from ..values import LyslynBuiltin


def sha256_hash(text: str) -> str:
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


def md5_hash(text: str) -> str:
    return hashlib.md5(str(text).encode("utf-8")).hexdigest()


def hmac_sha256(secret: str, message: str) -> str:
    return hmac.new(
        str(secret).encode("utf-8"),
        str(message).encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def random_token(num_bytes: int = 32) -> str:
    return secrets.token_hex(int(num_bytes))


def generate_uuid() -> str:
    return str(uuid.uuid4())


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"{salt}:{dk.hex()}"


def verify_password(password: str, hashed_str: str) -> bool:
    try:
        salt, dk_hex = hashed_str.split(":", 1)
        test_dk = hashlib.pbkdf2_hmac("sha256", str(password).encode("utf-8"), salt.encode("utf-8"), 100000)
        return hmac.compare_digest(test_dk.hex(), dk_hex)
    except Exception:
        return False


def export_module() -> Dict[str, Any]:
    return {
        "sha256": LyslynBuiltin("sha256", sha256_hash, arity=1),
        "md5": LyslynBuiltin("md5", md5_hash, arity=1),
        "hmac": LyslynBuiltin("hmac", hmac_sha256, arity=2),
        "token": LyslynBuiltin("token", random_token),
        "uuid": LyslynBuiltin("uuid", generate_uuid, arity=0),
        "hash_password": LyslynBuiltin("hash_password", hash_password, arity=1),
        "verify_password": LyslynBuiltin("verify_password", verify_password, arity=2),
    }
