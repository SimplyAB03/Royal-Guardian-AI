from __future__ import annotations
import base64, hashlib, json
from cryptography.fernet import Fernet, InvalidToken
from royal_guardian.core.config import settings

def _fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(settings.encryption_secret.encode()).digest())
    return Fernet(key)

def encrypt_json(value: dict) -> str:
    return _fernet().encrypt(json.dumps(value, separators=(",", ":")).encode()).decode()

def decrypt_json(value: str) -> dict:
    try:
        return json.loads(_fernet().decrypt(value.encode()).decode())
    except (InvalidToken, ValueError, json.JSONDecodeError):
        return {}
