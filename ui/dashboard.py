from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QProgressBar
from PySide6.QtCore import Qt

from ui.widgets.health_card import HealthCard


class Dashboard(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setSpacing(18)

        title = QLabel("⚜ Royal Guardian")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Your AI IT technician for Windows")
        subtitle.setObjectName("Muted")
        subtitle.setAlignment(Qt.AlignCenter)

        self.scan_status = QLabel("Guardian Engine ready.")
        self.scan_status.setObjectName("Muted")
        self.scan_status.setAlignment(Qt.AlignCenter)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.hide()

        self.health_card = HealthCard()

        self.quick_scan_btn = QPushButton("🔍 Quick Scan")

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(self.scan_status)
        layout.addWidget(self.progress)
        layout.addWidget(self.health_card)
        layout.addWidget(self.quick_scan_btn)
        layout.addStretch()

    def start_scan_ui(self):
        self.progress.show()
        self.progress.setValue(5)
        self.scan_status.setText("⚜ Initializing Guardian Engine...")
        self.health_card.summary.setText("Scanning system modules...")

    def set_scan_progress(self, text, value):
        self.progress.setValue(value)
        self.scan_status.setText(text)

    def finish_scan_ui(self):
        self.progress.setValue(100)
        self.scan_status.setText("✅ Scan complete.")

    def update_scan(self, scan):
        self.health_card.update_data(scan)