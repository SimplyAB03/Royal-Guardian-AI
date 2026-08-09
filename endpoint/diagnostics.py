from __future__ import annotations

import platform
import socket
from datetime import datetime, timezone

import psutil


def collect() -> dict:
    boot = datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc)
    memory = psutil.virtual_memory()
    drives = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            drives.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "filesystem": part.fstype,
                "total_gb": round(usage.total / 1024**3, 2),
                "free_gb": round(usage.free / 1024**3, 2),
                "used_percent": usage.percent,
            })
        except (PermissionError, OSError):
            continue
    adapters = []
    stats = psutil.net_if_stats()
    for name, addresses in psutil.net_if_addrs().items():
        adapters.append({
            "name": name,
            "is_up": bool(stats.get(name).isup) if stats.get(name) else None,
            "addresses": [{"family": str(a.family), "address": a.address} for a in addresses],
        })
    processes = []
    for p in psutil.process_iter(["pid", "name", "memory_percent", "cpu_percent"]):
        try:
            processes.append(p.info)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    processes.sort(key=lambda x: float(x.get("memory_percent") or 0), reverse=True)
    return {
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "cpu_percent": psutil.cpu_percent(interval=0.2),
        "ram_percent": memory.percent,
        "uptime_seconds": int((datetime.now(timezone.utc) - boot).total_seconds()),
        "drives": drives,
        "network_adapters": adapters,
        "top_processes": processes[:20],
    }
