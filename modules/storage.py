import psutil

def run():
    drives = []
    issues = []
    status = "healthy"
    priority = 0

    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
        except PermissionError:
            continue

        drive = {
            "device": part.device,
            "mountpoint": part.mountpoint,
            "filesystem": part.fstype,
            "total_gb": round(usage.total / (1024**3), 1),
            "free_gb": round(usage.free / (1024**3), 1),
            "used_percent": usage.percent
        }
        drives.append(drive)

        if usage.percent >= 90:
            status = "critical"
            priority = 1
            issues.append({
                "title": f"Drive {part.device} is almost full",
                "simple": "Your storage is almost full. This can slow down Windows and cause updates to fail.",
                "technical": f"{part.device} is {usage.percent}% used.",
                "recommendation": "Free up space or move large files to another drive."
            })
        elif usage.percent >= 75 and status != "critical":
            status = "warning"
            priority = max(priority, 2)
            issues.append({
                "title": f"Drive {part.device} is getting full",
                "simple": "Your storage is starting to fill up. Windows works better with free space.",
                "technical": f"{part.device} is {usage.percent}% used.",
                "recommendation": "Consider deleting temporary files or unused downloads."
            })

    return {
        "module": "storage",
        "title": "Storage Health",
        "status": status,
        "priority": priority,
        "summary": "Checks all accessible drives and free space.",
        "data": {
            "drives": drives
        },
        "issues": issues
    }