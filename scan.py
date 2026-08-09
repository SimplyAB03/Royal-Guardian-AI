import json
from pathlib import Path

from guardian_ai.summary import build_summary
from engine.comparison import compare_to_previous
from engine.scanner import run_guardian_scan
from engine.timeline import save_scan_history
from core.report_generator import generate_html_report

scan = run_guardian_scan()
ai_summary = build_summary(scan)

# Keep compatibility with current UI
diagnostics = {}

for module in scan["modules"]:
    if module["module"] == "system_basic":
        diagnostics.update(module["data"])
    elif module["module"] == "storage":
        drives = module["data"].get("drives", [])
        diagnostics["drives"] = drives
        if drives:
            diagnostics["disk_free_gb"] = drives[0]["free_gb"]
            diagnostics["disk_used_percent"] = drives[0]["used_percent"]
    elif module["module"] == "usb_devices":
        diagnostics["usb_devices"] = module["data"].get("usb_devices", [])

result = {
    "ai_summary": ai_summary,
    "scan_time": scan["scan_time"],
    "diagnostics": diagnostics,
    "health": {
        "score": scan["score"],
        "issues": [
            {
                "severity": "medium",
                "title": issue["title"],
                "explanation": issue["simple"],
                "recommendation": issue["recommendation"]
            }
            for issue in scan["issues"]
        ]
    },
    "guardian_engine": scan
}

report_path = generate_html_report(result)
result["report_path"] = report_path
history_path = save_scan_history(result)
result["history_path"] = history_path
comparison = compare_to_previous(result)
result["comparison"] = comparison
Path("data").mkdir(exist_ok=True)

with open("data/latest_scan.json", "w", encoding="utf-8") as f:
    json.dump(result, f, indent=4)

print(json.dumps(result, indent=4))