from __future__ import annotations
import base64, hashlib, json, os, tempfile, urllib.request
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# The release pipeline injects this through RG_UPDATE_PUBLIC_KEY_B64.
def _public_key() -> Ed25519PublicKey:
    raw=os.getenv("RG_UPDATE_PUBLIC_KEY_B64","")
    if not raw: raise RuntimeError("RG_UPDATE_PUBLIC_KEY_B64 is not configured")
    return Ed25519PublicKey.from_public_bytes(base64.b64decode(raw))

def verify_manifest(manifest_bytes:bytes, signature_b64:str)->dict:
    _public_key().verify(base64.b64decode(signature_b64),manifest_bytes)
    return json.loads(manifest_bytes)

def download_verified(url:str, expected_sha256:str)->Path:
    out=Path(tempfile.mkdtemp(prefix="rg-update-"))/"update.bin"
    with urllib.request.urlopen(url,timeout=60) as r, out.open("wb") as f:
        while chunk:=r.read(1024*1024): f.write(chunk)
    digest=hashlib.sha256(out.read_bytes()).hexdigest()
    if digest.lower()!=expected_sha256.lower():
        out.unlink(missing_ok=True); raise RuntimeError("Downloaded update hash mismatch")
    return out
