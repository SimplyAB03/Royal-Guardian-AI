from __future__ import annotations

import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any


def _windows_only() -> dict[str, Any] | None:
    if platform.system().lower() != "windows":
        return {"ok": False, "error": "This action is only supported on Windows"}
    return None


def _run(cmd: list[str], timeout: int = 30) -> dict[str, Any]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, shell=False)
        return {"ok": p.returncode == 0, "returncode": p.returncode, "stdout": p.stdout[-4000:], "stderr": p.stderr[-4000:]}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def flush_dns(_: dict) -> dict:
    guard = _windows_only()
    if guard:
        return guard
    return _run(["ipconfig", "/flushdns"])


def renew_ip(_: dict) -> dict:
    guard = _windows_only()
    if guard:
        return guard
    release = _run(["ipconfig", "/release"], timeout=40)
    renew = _run(["ipconfig", "/renew"], timeout=60)
    return {"ok": bool(release.get("ok") and renew.get("ok")), "release": release, "renew": renew}


def restart_service(parameters: dict) -> dict:
    guard = _windows_only()
    if guard:
        return guard
    allowed = {"spooler", "wuauserv", "dnscache"}
    service = str(parameters.get("service", "")).lower()
    if service not in allowed:
        return {"ok": False, "error": "Service is not allowlisted"}
    return _run(["powershell", "-NoProfile", "-Command", f"Restart-Service -Name '{service}' -ErrorAction Stop"], timeout=45)


def terminate_process(parameters: dict) -> dict:
    guard = _windows_only()
    if guard:
        return guard
    allowed = {"outlook.exe", "teams.exe", "notepad.exe", "msedge.exe", "chrome.exe"}
    process = str(parameters.get("process", "")).lower()
    if process not in allowed:
        return {"ok": False, "error": "Process is not allowlisted"}
    return _run(["taskkill", "/IM", process, "/F"])


def clear_temp(parameters: dict) -> dict:
    # Deliberately constrained to the current user's temp directory.
    root = Path(tempfile.gettempdir()).resolve()
    removed = 0
    failures = 0
    for child in list(root.iterdir()):
        try:
            resolved = child.resolve()
            if root not in resolved.parents and resolved != root:
                failures += 1
                continue
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child, ignore_errors=False)
            else:
                child.unlink(missing_ok=True)
            removed += 1
        except Exception:
            failures += 1
    return {"ok": True, "removed_entries": removed, "failed_entries": failures, "scope": str(root)}


def reboot(_: dict) -> dict:
    guard = _windows_only()
    if guard:
        return guard
    # This action is only executed after the cloud-side approval gate.
    return _run(["shutdown", "/r", "/t", "15", "/c", "Royal Guardian approved restart"], timeout=10)


ACTIONS = {
    "network.flush_dns": {"risk": "low", "approval_required": False, "handler": flush_dns},
    "network.renew_ip": {"risk": "medium", "approval_required": True, "handler": renew_ip},
    "windows.restart_service": {"risk": "medium", "approval_required": True, "handler": restart_service},
    "process.terminate": {"risk": "medium", "approval_required": True, "handler": terminate_process},
    "storage.clear_user_temp": {"risk": "medium", "approval_required": True, "handler": clear_temp},
    "system.reboot": {"risk": "high", "approval_required": True, "handler": reboot},
}


def execute_action(action_id: str, parameters: dict | None = None) -> dict:
    action = ACTIONS.get(action_id)
    if not action:
        return {"ok": False, "error": "Unknown or non-allowlisted action"}
    return action["handler"](parameters or {})
