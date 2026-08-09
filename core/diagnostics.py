import platform
import socket
import psutil
from datetime import datetime

def get_drives():
    drives = []

    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            drives.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "filesystem": part.fstype,
                "total_gb": round(usage.total / (1024**3), 1),
                "free_gb": round(usage.free / (1024**3), 1),
                "used_percent": usage.percent
            })
        except PermissionError:
            continue

    return drives

def get_usb_devices():
    usb_like = []

    for part in psutil.disk_partitions(all=False):
        opts = part.opts.lower()
        if "removable" in opts or "cdrom" in opts:
            usb_like.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "type": "removable"
            })

    return usb_like

def get_diagnostics():
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    disk = psutil.disk_usage("C:\\")

    return {
        "computer_name": socket.gethostname(),
        "windows": platform.platform(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "ram_percent": psutil.virtual_memory().percent,
        "disk_free_gb": round(disk.free / (1024**3), 1),
        "disk_used_percent": disk.percent,
        "uptime_days": uptime.days,
        "last_boot": boot_time.strftime("%Y-%m-%d %I:%M %p"),
        "drives": get_drives(),
        "usb_devices": get_usb_devices()
    }