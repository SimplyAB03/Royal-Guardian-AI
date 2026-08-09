import subprocess
import json

def run_powershell(command):
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            timeout=15
        )
        return completed.stdout.strip(), completed.stderr.strip()
    except Exception as e:
        return "", str(e)

def run():
    issues = []
    status = "healthy"
    priority = 0

    command = """
    $items = Get-CimInstance Win32_StartupCommand | Select-Object Name, Command, Location, User
    $items | ConvertTo-Json -Compress
    """

    stdout, stderr = run_powershell(command)

    startup_items = []
    if stdout:
        try:
            parsed = json.loads(stdout)
            startup_items = parsed if isinstance(parsed, list) else [parsed]
        except Exception:
            startup_items = []

    count = len(startup_items)

    if count >= 20:
        status = "warning"
        priority = 2
        issues.append({
            "priority": 2,
            "title": "Many startup apps detected",
            "simple": "A lot of apps are set to open when Windows starts. This can make startup slower.",
            "technical": f"{count} startup entries detected.",
            "recommendation": "Review startup apps and disable anything unnecessary."
        })

    return {
        "module": "startup_apps",
        "title": "Startup Apps",
        "status": status,
        "priority": priority,
        "summary": "Checks apps configured to start with Windows.",
        "data": {
            "count": count,
            "items": startup_items[:25],
            "error": stderr or None
        },
        "issues": issues
    }