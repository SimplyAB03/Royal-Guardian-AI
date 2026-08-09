from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel


class HealthCard(QFrame):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        title = QLabel("Computer Health")
        title.setObjectName("Muted")

        self.score = QLabel("--")
        self.score.setObjectName("Score")

        self.summary = QLabel("Run a scan to check this PC.")
        self.summary.setWordWrap(True)

        layout.addWidget(title)
        layout.addWidget(self.score)
        layout.addWidget(self.summary)

    def update_data(self, scan):
        score = scan.get("health", {}).get("score", "--")
        ai = scan.get("ai_summary", {})

        self.score.setText(str(score))
        self.summary.setText(ai.get("headline", "Scan complete."))