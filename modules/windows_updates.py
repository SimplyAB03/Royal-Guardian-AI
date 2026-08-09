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
    $rebootRequired = Test-Path "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\WindowsUpdate\\Auto Update\\RebootRequired"
    $service = Get-Service -Name wuauserv -ErrorAction SilentlyContinue
    $obj = [PSCustomObject]@{
        RebootRequired = $rebootRequired
        WindowsUpdateService = if ($service) { $service.Status.ToString() } else { "NotFound" }
    }
    $obj | ConvertTo-Json -Compress
    """

    stdout, stderr = run_powershell(command)

    data = {
        "available": False,
        "error": stderr or None
    }

    if stdout:
        try:
            data = json.loads(stdout)
            data["available"] = True
        except Exception as e:
            data = {
                "available": False,
                "error": str(e),
                "raw": stdout
            }

    if not data.get("available"):
        status = "warning"
        priority = 2
        issues.append({
            "priority": 2,
            "title": "Unable to verify Windows Update",
            "simple": "Royal Guardian could not confirm the current Windows Update status.",
            "technical": data.get("error") or "Windows Update check failed.",
            "recommendation": "Open Windows Update and check for updates manually."
        })
    else:
        if data.get("RebootRequired"):
            status = "warning"
            priority = 2
            issues.append({
                "priority": 2,
                "title": "Restart required for Windows Update",
                "simple": "Windows has updates waiting to finish. Restarting will complete them.",
                "technical": "Windows Update RebootRequired registry key is present.",
                "recommendation": "Restart the computer when convenient."
            })

        if data.get("WindowsUpdateService") in ["Disabled", "NotFound"]:
            status = "warning"
            priority = 2
            issues.append({
                "priority": 2,
                "title": "Windows Update service may not be running",
                "simple": "Windows Update may not be able to check for updates properly.",
                "technical": f"wuauserv status: {data.get('WindowsUpdateService')}",
                "recommendation": "Open Services or Windows Update and verify updates are working."
            })

    return {
        "module": "windows_updates",
        "title": "Windows Updates",
        "status": status,
        "priority": priority,
        "summary": "Checks whether Windows Update needs a restart and whether the update service is available.",
        "data": data,
        "issues": issues
    }