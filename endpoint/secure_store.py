from __future__ import annotations
import base64, json, os, platform
from pathlib import Path

CONFIG_DIR = Path(os.getenv("PROGRAMDATA", Path.home())) / "RoyalGuardian"
CONFIG_FILE = CONFIG_DIR / "device.json"

def _dpapi_protect(data: bytes) -> bytes:
    if platform.system().lower() != "windows":
        return data
    try:
        import win32crypt  # type: ignore
        return win32crypt.CryptProtectData(data, "Royal Guardian device credential", None, None, None, 0)[1]
    except Exception as exc:
        raise RuntimeError("Windows DPAPI protection requires pywin32 in the packaged endpoint build") from exc

def _dpapi_unprotect(data: bytes) -> bytes:
    if platform.system().lower() != "windows":
        return data
    try:
        import win32crypt  # type: ignore
        return win32crypt.CryptUnprotectData(data, None, None, None, 0)[1]
    except Exception as exc:
        raise RuntimeError("Unable to decrypt Royal Guardian device credential with Windows DPAPI") from exc

def save(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    token=str(config.get("device_token", ""))
    safe={k:v for k,v in config.items() if k!="device_token"}
    if token:
        safe["device_token_protected"] = base64.b64encode(_dpapi_protect(token.encode())).decode()
    tmp=CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(safe, indent=2),encoding="utf-8")
    os.replace(tmp,CONFIG_FILE)
    try: os.chmod(CONFIG_FILE,0o600)
    except OSError: pass

def load() -> dict:
    raw=json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    protected=raw.pop("device_token_protected","")
    if protected: raw["device_token"]=_dpapi_unprotect(base64.b64decode(protected)).decode()
    return raw

def clear() -> None:
    CONFIG_FILE.unlink(missing_ok=True)
