from __future__ import annotations

import hashlib
import json
import os
import platform
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from endpoint.secure_store import save as secure_save, load as secure_load

from endpoint.actions import execute_action
from endpoint.diagnostics import collect

CONFIG_DIR = Path(os.getenv("PROGRAMDATA", Path.home())) / "RoyalGuardian"
CONFIG_FILE = CONFIG_DIR / "device.json"


def fingerprint() -> str:
    material = f"{socket.gethostname()}|{platform.platform()}|{os.getenv('COMPUTERNAME','')}|{os.getenv('USERNAME','')}"
    return hashlib.sha256(material.encode()).hexdigest()


def request_json(method: str, url: str, body: dict | None = None, token: str | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json", "User-Agent": "RoyalGuardianEndpoint/0.2"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def save_config(config: dict) -> None:
    secure_save(config)


def load_config() -> dict:
    return secure_load()


def enroll(base_url: str, enrollment_token: str, name: str | None = None) -> dict:
    response = request_json("POST", f"{base_url.rstrip('/')}/api/devices/enroll", {
        "enrollment_token": enrollment_token,
        "name": name or socket.gethostname(),
        "fingerprint": fingerprint(),
        "platform": "windows",
    })
    config = {"base_url": base_url.rstrip("/"), "device_id": response["device_id"], "device_token": response["device_token"]}
    save_config(config)
    return config


def once(config: dict) -> None:
    base = config["base_url"]
    token = config["device_token"]
    request_json("POST", f"{base}/api/device/heartbeat", {"diagnostics": collect()}, token)
    command = request_json("GET", f"{base}/api/device/commands/next", token=token).get("command")
    if not command:
        return
    result = execute_action(command["action_id"], command.get("parameters") or {})
    payload = {"ok": bool(result.get("ok")), "result": result if result.get("ok") else {}, "error": result.get("error") if not result.get("ok") else None}
    request_json("POST", f"{base}/api/device/commands/{command['id']}/result", payload, token)


def run_forever(interval: int = 20) -> None:
    config = load_config()
    while True:
        try:
            once(config)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            print(f"Royal Guardian endpoint communication error: {exc}")
        time.sleep(interval)
