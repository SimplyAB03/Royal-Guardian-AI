import sys
import json
from pathlib import Path

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QProgressBar

from core.scan_bridge import ScanBridge

BASE_DIR = Path(__file__).resolve().parent


class ScanThread(QThread):
    def __init__(self):
        super().__init__()
        self.bridge = ScanBridge()
        self.bridge.moveToThread(self)

    def run(self):
        self.bridge.startScan()


class RoyalGuardian(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Royal Guardian Native")
        self.resize(900, 600)
        self.setStyleSheet("""
            QWidget { background:#0A0A0F; color:#F0E6C8; font-family:Segoe UI; }
            QLabel#title { color:#FFD700; font-size:28px; font-weight:800; }
            QLabel#score { color:#22C55E; font-size:72px; font-weight:800; }
            QPushButton { background:#C9A227; color:#0A0A0F; border:none; padding:12px; border-radius:8px; font-weight:700; }
            QProgressBar { border:1px solid #3A2E10; border-radius:8px; height:20px; background:#1E1E2E; text-align:center; }
            QProgressBar::chunk { background:#C9A227; border-radius:8px; }
        """)

        root = QWidget()
        self.layout = QVBoxLayout(root)
        self.layout.setAlignment(Qt.AlignCenter)
        self.setCentralWidget(root)

        self.title = QLabel("⚜ Royal Guardian")
        self.title.setObjectName("title")
        self.title.setAlignment(Qt.AlignCenter)

        self.status = QLabel("Ready to scan.")
        self.status.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setValue(0)

        self.score = QLabel("--")
        self.score.setObjectName("score")
        self.score.setAlignment(Qt.AlignCenter)

        self.summary = QLabel("Run a scan to check this PC.")
        self.summary.setAlignment(Qt.AlignCenter)
        self.summary.setWordWrap(True)

        self.button = QPushButton("🔍 Start Guardian Scan")
        self.button.clicked.connect(self.start_scan)

        self.layout.addWidget(self.title)
        self.layout.addWidget(self.status)
        self.layout.addWidget(self.progress)
        self.layout.addWidget(self.score)
        self.layout.addWidget(self.summary)
        self.layout.addWidget(self.button)

    def start_scan(self):
        self.button.setDisabled(True)
        self.button.setText("⚜ Scanning...")
        self.progress.setValue(0)
        self.status.setText("Initializing Guardian Engine...")

        self.thread = ScanThread()
        self.thread.bridge.progressChanged.connect(self.on_progress)
        self.thread.bridge.finished.connect(self.on_finished)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def on_progress(self, module, percent, status):
        self.progress.setValue(percent)
        self.status.setText(f"{module} — {status}")

    def on_finished(self, result):
        self.score.setText(str(result["score"]))

        if result["issues"]:
            first = result["issues"][0]
            self.summary.setText(first["simple"])
        else:
            self.summary.setText("Your computer looks excellent. No action is required right now.")

        self.button.setDisabled(False)
        self.button.setText("🔍 Start Guardian Scan")
        self.status.setText("Scan complete.")
        self.thread.quit()


app = QApplication(sys.argv)
window = RoyalGuardian()
window.show()
sys.exit(app.exec())