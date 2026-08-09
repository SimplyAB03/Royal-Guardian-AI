import json
from pathlib import Path
from datetime import datetime

HISTORY_DIR = Path("data/history")

def save_scan_history(result):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"scan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path = HISTORY_DIR / filename

    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=4)

    return str(path)

def load_scan_history(limit=10):
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    scans = []
    for path in sorted(HISTORY_DIR.glob("scan_*.json"), reverse=True)[:limit]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                scan = json.load(f)
                scans.append({
                    "file": path.name,
                    "scan_time": scan.get("scan_time"),
                    "score": scan.get("health", {}).get("score"),
                    "issues": len(scan.get("health", {}).get("issues", [])),
                    "report_path": scan.get("report_path")
                })
        except Exception:
            continue

    return scans