import socket
import psutil

def run():
    issues = []
    status = "healthy"
    priority = 0

    adapters = []
    for name, stats in psutil.net_if_stats().items():
        if stats.isup:
            adapters.append({
                "name": name,
                "speed_mbps": stats.speed,
                "is_up": stats.isup
            })

    internet_ok = False
    dns_ok = False

    try:
        socket.gethostbyname("microsoft.com")
        dns_ok = True
    except Exception:
        dns_ok = False

    try:
        sock = socket.create_connection(("1.1.1.1", 53), timeout=3)
        sock.close()
        internet_ok = True
    except Exception:
        internet_ok = False

    if not internet_ok:
        status = "critical"
        priority = 1
        issues.append({
            "priority": 1,
            "title": "Internet connection issue detected",
            "simple": "Royal Guardian could not confirm that this computer can reach the internet.",
            "technical": "Connection test to 1.1.1.1:53 failed.",
            "recommendation": "Check Wi-Fi, Ethernet, router, or VPN connection."
        })
    elif not dns_ok:
        status = "warning"
        priority = 2
        issues.append({
            "priority": 2,
            "title": "DNS issue detected",
            "simple": "Your internet may be connected, but website names may not resolve properly.",
            "technical": "DNS lookup for microsoft.com failed.",
            "recommendation": "Check DNS settings or restart the router."
        })

    return {
        "module": "network",
        "title": "Network Connectivity",
        "status": status,
        "priority": priority,
        "summary": "Checks active network adapters, DNS, and basic internet reachability.",
        "data": {
            "internet_ok": internet_ok,
            "dns_ok": dns_ok,
            "active_adapters": adapters
        },
        "issues": issues
    }