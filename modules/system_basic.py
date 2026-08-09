import platform
import socket
import psutil
from datetime import datetime

def run():
    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time
    memory = psutil.virtual_memory()

    status = "healthy"
    priority = 0
    issues = []

    if uptime.days >= 7:
        status = "warning"
        priority = 2
        issues.append({
            "title": "Restart recommended",
            "simple": "Your computer has been running for several days. Restarting can improve performance and finish pending updates.",
            "technical": f"System uptime is {uptime.days} days.",
            "recommendation": "Restart when convenient."
        })

    if memory.percent >= 85:
        status = "warning"
        priority = max(priority, 2)
        issues.append({
            "title": "High memory usage",
            "simple": "Your computer is using a lot of RAM, which may make it feel slower.",
            "technical": f"RAM usage is {memory.percent}%.",
            "recommendation": "Close unused apps or restart the computer."
        })

    return {
        "module": "system_basic",
        "title": "Basic System Health",
        "status": status,
        "priority": priority,
        "summary": "Checks uptime, memory, CPU, and Windows version.",
        "data": {
            "computer_name": socket.gethostname(),
            "windows": platform.platform(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "ram_percent": memory.percent,
            "uptime_days": uptime.days,
            "last_boot": boot_time.strftime("%Y-%m-%d %I:%M %p")
        },
        "issues": issues
    }