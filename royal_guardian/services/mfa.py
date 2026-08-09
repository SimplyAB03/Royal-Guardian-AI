from __future__ import annotations
import base64, hashlib, hmac, secrets, struct, time, urllib.parse


def generate_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip("=")


def _decode(secret: str) -> bytes:
    pad = "=" * ((8 - len(secret) % 8) % 8)
    return base64.b32decode((secret.upper() + pad).encode())


def totp(secret: str, at: int | None = None, step: int = 30, digits: int = 6) -> str:
    counter = int((at if at is not None else time.time()) // step)
    digest = hmac.new(_decode(secret), struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = (struct.unpack(">I", digest[offset:offset+4])[0] & 0x7FFFFFFF) % (10 ** digits)
    return f"{value:0{digits}d}"


def verify_totp(secret: str, code: str, at: int | None = None, window: int = 1) -> bool:
    now = int(at if at is not None else time.time())
    clean = "".join(ch for ch in str(code) if ch.isdigit())
    return any(hmac.compare_digest(totp(secret, now + delta * 30), clean) for delta in range(-window, window + 1))


def provisioning_uri(secret: str, email: str, issuer: str = "Royal Guardian") -> str:
    label = urllib.parse.quote(f"{issuer}:{email}")
    return f"otpauth://totp/{label}?secret={urllib.parse.quote(secret)}&issuer={urllib.parse.quote(issuer)}&algorithm=SHA1&digits=6&period=30"
