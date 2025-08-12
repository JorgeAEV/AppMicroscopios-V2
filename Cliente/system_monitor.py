from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from network import NetworkClient

class SystemMonitor(QObject):
    status_updated = pyqtSignal(dict)

    def __init__(self, poll_interval_ms=2000):
        super().__init__()
        self.client = NetworkClient()
        self.timer = QTimer()
        self.timer.timeout.connect(self.poll_status)
        self.timer.start(poll_interval_ms)

    def poll_status(self):
        status = self.client.get_status()
        self.status_updated.emit(status)
