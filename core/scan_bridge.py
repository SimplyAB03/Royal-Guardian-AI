from PySide6.QtCore import QObject, Signal, Slot
from engine.scanner import run_guardian_scan


class ScanBridge(QObject):

    progressChanged = Signal(str, int, str)
    finished = Signal(dict)

    @Slot()
    def startScan(self):

        def callback(module, percent, status):
            self.progressChanged.emit(module, percent, status)

        result = run_guardian_scan(progress_callback=callback)

        self.finished.emit(result)