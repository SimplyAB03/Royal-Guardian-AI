import sys
import json
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import QThread, Signal, QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox

from resources.styles.variables import APP_STYLE
from ui.dashboard import Dashboard

BASE_DIR = PROJECT_ROOT


class ScanWorker(QThread):
    finished = Signal(dict)
    failed = Signal(str)

    def run(self):
        try:
            subprocess.run(
                [sys.executable, str(BASE_DIR / "scan.py")],
                cwd=BASE_DIR,
                check=True
            )

            path = BASE_DIR / "data" / "latest_scan.json"
            with open(path, "r", encoding="utf-8") as f:
                scan = json.load(f)

            self.finished.emit(scan)

        except Exception as e:
            self.failed.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Royal Guardian")
        self.resize(1100, 720)
        self.setStyleSheet(APP_STYLE)

        self.dashboard = Dashboard()
        self.setCentralWidget(self.dashboard)

        self.dashboard.quick_scan_btn.clicked.connect(self.run_scan)

        self.scan_steps = [
            ("Checking system health...", 14),
            ("Scanning storage devices...", 28),
            ("Checking USB devices...", 42),
            ("Verifying Windows Defender...", 57),
            ("Checking Windows Update...", 71),
            ("Reviewing startup apps...", 85),
            ("Testing network connection...", 96),
        ]
        self.step_index = 0

        self.load_last_scan()

    def run_scan(self):
        self.dashboard.quick_scan_btn.setText("⚜ Scanning...")
        self.dashboard.quick_scan_btn.setDisabled(True)
        self.dashboard.start_scan_ui()

        self.step_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.advance_scan_animation)
        self.timer.start(450)

        self.worker = ScanWorker()
        self.worker.finished.connect(self.scan_finished)
        self.worker.failed.connect(self.scan_failed)
        self.worker.start()

    def advance_scan_animation(self):
        if self.step_index < len(self.scan_steps):
            text, value = self.scan_steps[self.step_index]
            self.dashboard.set_scan_progress(text, value)
            self.step_index += 1

    def scan_finished(self, scan):
        if hasattr(self, "timer"):
            self.timer.stop()

        self.dashboard.update_scan(scan)
        self.dashboard.finish_scan_ui()
        self.dashboard.quick_scan_btn.setText("🔍 Quick Scan")
        self.dashboard.quick_scan_btn.setDisabled(False)

    def scan_failed(self, error):
        if hasattr(self, "timer"):
            self.timer.stop()

        self.dashboard.quick_scan_btn.setText("🔍 Quick Scan")
        self.dashboard.quick_scan_btn.setDisabled(False)
        QMessageBox.critical(self, "Scan Failed", error)

    def load_last_scan(self):
        path = BASE_DIR / "data" / "latest_scan.json"
        if not path.exists():
            return

        with open(path, "r", encoding="utf-8") as f:
            scan = json.load(f)

        self.dashboard.update_scan(scan)


def run():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()