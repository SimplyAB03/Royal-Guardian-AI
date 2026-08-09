import sys
import json
import subprocess
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtCore import QUrl, QObject, Slot
from PySide6.QtWebChannel import QWebChannel

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent

HTML_FILE = BASE_DIR / "royal_guardian_ui_preview.html"


class Bridge(QObject):
    @Slot(result=str)
    def runQuickScan(self):
        subprocess.run([sys.executable, str(BASE_DIR / "scan.py")], cwd=BASE_DIR)
        scan_file = BASE_DIR / "data" / "latest_scan.json"

        with open(scan_file, "r", encoding="utf-8") as f:
            return json.dumps(json.load(f))

    @Slot(result=str)
    def loadLastScan(self):
        scan_file = BASE_DIR / "data" / "latest_scan.json"

        if not scan_file.exists():
            return json.dumps({
                "has_scan": False,
                "message": "No previous scan found."
            })

        with open(scan_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["has_scan"] = True
        return json.dumps(data)

    @Slot(result=str)
    def getReports(self):
        reports_dir = BASE_DIR / "reports"
        reports_dir.mkdir(exist_ok=True)

        reports = []
        for path in sorted(reports_dir.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True):
            reports.append({
                "name": path.name,
                "path": str(Path("reports") / path.name),
                "modified": path.stat().st_mtime
            })

        return json.dumps(reports)

    @Slot(str, result=str)
    def openReport(self, report_path):
        try:
            full_path = BASE_DIR / report_path

            if not full_path.exists():
                return "Report not found: " + str(full_path)

            os.startfile(str(full_path))
            return "opened"
        except Exception as e:
            return "error: " + str(e)


app = QApplication(sys.argv)

window = QMainWindow()
window.setWindowTitle("Royal Guardian")
window.resize(1100, 720)

view = QWebEngineView()

channel = QWebChannel()
bridge = Bridge()
channel.registerObject("bridge", bridge)
view.page().setWebChannel(channel)

view.load(QUrl.fromLocalFile(str(HTML_FILE)))

window.setCentralWidget(view)
window.show()

sys.exit(app.exec())
