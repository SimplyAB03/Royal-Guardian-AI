import subprocess
import json

def run_powershell(command):
    try:
        completed = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            capture_output=True,
            text=True,
            timeout=10
        )
        return completed.stdout.strip(), completed.stderr.strip()
    except Exception as e:
        return "", str(e)

def run():
    issues = []
    status = "healthy"
    priority = 0

    command = """
    $mp = Get-MpComputerStatus
    $obj = [PSCustomObject]@{
        AntivirusEnabled = $mp.AntivirusEnabled
        RealTimeProtectionEnabled = $mp.RealTimeProtectionEnabled
        AntispywareEnabled = $mp.AntispywareEnabled
        DefenderSignaturesAge = $mp.AntivirusSignatureAge
        LastQuickScan = $mp.QuickScanEndTime
        LastFullScan = $mp.FullScanEndTime
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
            "title": "Unable to verify Windows Defender",
            "simple": "Royal Guardian could not confirm the current Windows Defender status.",
            "technical": data.get("error") or "Get-MpComputerStatus failed.",
            "recommendation": "Open Windows Security and confirm virus protection is enabled."
        })
    else:
        if not data.get("AntivirusEnabled") or not data.get("RealTimeProtectionEnabled"):
            status = "critical"
            priority = 1
            issues.append({
                "priority": 1,
                "title": "Windows Defender protection may be disabled",
                "simple": "Your computer may not have active real-time antivirus protection.",
                "technical": f"AntivirusEnabled={data.get('AntivirusEnabled')}, RealTimeProtectionEnabled={data.get('RealTimeProtectionEnabled')}",
                "recommendation": "Open Windows Security and turn real-time protection back on."
            })

        if data.get("DefenderSignaturesAge") is not None and data.get("DefenderSignaturesAge") > 7:
            if status != "critical":
                status = "warning"
                priority = 2
            issues.append({
                "priority": 2,
                "title": "Defender definitions may be outdated",
                "simple": "Your antivirus protection may not have the newest threat definitions.",
                "technical": f"Signature age is {data.get('DefenderSignaturesAge')} days.",
                "recommendation": "Run Windows Update or update protection definitions in Windows Security."
            })

    return {
        "module": "defender",
        "title": "Windows Defender",
        "status": status,
        "priority": priority,
        "summary": "Checks Microsoft Defender antivirus and real-time protection status.",
        "data": data,
        "issues": issues
    }