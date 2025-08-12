from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QGridLayout
from PyQt6.QtCore import Qt
from system_monitor import SystemMonitor
from network import NetworkClient

class TabBienvenida(QWidget):
    def __init__(self):
        super().__init__()

        self.client = NetworkClient()
        self.system_monitor = SystemMonitor()
        self.system_monitor.status_updated.connect(self.update_status)

        self.init_ui()
        self.load_cameras()

    def init_ui(self):
        layout = QVBoxLayout()

        # Cámaras detectadas
        self.lbl_cameras = QLabel("Cámaras detectadas: Cargando...")
        layout.addWidget(self.lbl_cameras)

        # Panel de estado Raspberry Pi
        estado_group = QGroupBox("Estado Raspberry Pi")
        estado_layout = QGridLayout()

        self.lbl_temp = QLabel("Temperatura CPU: - °C")
        self.lbl_cpu = QLabel("CPU Uso: - %")
        self.lbl_ram = QLabel("RAM Usada: - MB / - MB")
        self.lbl_disk = QLabel("Almacenamiento Libre: - GB")

        estado_layout.addWidget(self.lbl_temp, 0, 0)
        estado_layout.addWidget(self.lbl_cpu, 1, 0)
        estado_layout.addWidget(self.lbl_ram, 2, 0)
        estado_layout.addWidget(self.lbl_disk, 3, 0)

        estado_group.setLayout(estado_layout)
        layout.addWidget(estado_group)

        layout.addStretch()
        self.setLayout(layout)

    def load_cameras(self):
        cameras = self.client.get_cameras()
        self.lbl_cameras.setText(f"Cámaras detectadas: {len(cameras)}")

    def update_status(self, status):
        temp = status.get('temperature_c', '-')
        cpu = status.get('cpu_percent', '-')
        ram_used = status.get('ram_used_mb', '-')
        ram_total = status.get('ram_total_mb', '-')
        disk_free = status.get('disk_free_gb', '-')

        self.lbl_temp.setText(f"Temperatura CPU: {temp} °C")
        self.lbl_cpu.setText(f"CPU Uso: {cpu} %")
        self.lbl_ram.setText(f"RAM Usada: {ram_used} MB / {ram_total} MB")
        self.lbl_disk.setText(f"Almacenamiento Libre: {disk_free} GB")
