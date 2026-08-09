from datetime import datetime

from engine.scoring import calculate_score
from engine.scan_queue import run_scan

MODULES = [
    "modules.system_basic",
    "modules.storage",
    "modules.usb_devices",
    "modules.defender",
    "modules.windows_updates",
    "modules.startup_apps",
    "modules.network"
]

def run_guardian_scan(progress_callback=None):
    module_results = run_scan(MODULES, callback=progress_callback)

    issues = []
    for result in module_results:
        issues.extend(result.get("issues", []))

    issues.sort(key=lambda x: x.get("priority", 99))

    return {
        "scan_time": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "score": calculate_score(module_results),
        "modules": module_results,
        "issues": issues
    }