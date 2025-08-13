from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QGridLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
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

        # === Banner de bienvenida ===
        banner = QLabel("🔬 MicroScope Viewer\nSistema de Monitoreo con Raspberry Pi 3B y Cámaras USB")
        banner.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner.setStyleSheet("""
            background-color: #0078D7;
            color: white;
            padding: 15px;
            border-radius: 8px;
        """)
        layout.addWidget(banner)

        # Cámaras detectadas
        self.lbl_cameras = QLabel("📷 Cámaras detectadas: Cargando...")
        self.lbl_cameras.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        layout.addWidget(self.lbl_cameras)

        # Panel de estado Raspberry Pi
        estado_group = QGroupBox("📟 Estado Raspberry Pi 3B")
        estado_group.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        estado_layout = QGridLayout()

        self.lbl_temp = QLabel("🌡️ Temperatura CPU: - °C")
        self.lbl_cpu = QLabel("🖥️ CPU Uso: - %")
        self.lbl_ram = QLabel("💾 RAM Usada: - MB / - MB")
        self.lbl_disk = QLabel("📂 Almacenamiento Libre: - GB")

        for lbl in [self.lbl_temp, self.lbl_cpu, self.lbl_ram, self.lbl_disk]:
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setStyleSheet("padding: 3px;")

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
        self.lbl_cameras.setText(f"📷 Cámaras detectadas: {len(cameras)}")

    def update_status(self, status):
        temp = status.get('temperature_c', '-')
        cpu = status.get('cpu_percent', '-')
        ram_used = status.get('ram_used_mb', '-')
        ram_total = status.get('ram_total_mb', '-')
        disk_free = status.get('disk_free_gb', '-')

        # Actualizar valores
        self.lbl_temp.setText(f"🌡️ Temperatura CPU: {temp} °C")
        self.lbl_cpu.setText(f"🖥️ CPU Uso: {cpu} %")
        self.lbl_ram.setText(f"💾 RAM Usada: {ram_used} MB / {ram_total} MB")
        self.lbl_disk.setText(f"📂 Almacenamiento Libre: {disk_free} GB")

        # Colores de advertencia
        if isinstance(temp, (int, float)) and temp >= 70:
            self.lbl_temp.setStyleSheet("color: red; font-weight: bold;")
        elif isinstance(temp, (int, float)) and temp >= 60:
            self.lbl_temp.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.lbl_temp.setStyleSheet("color: green;")

        if isinstance(cpu, (int, float)) and cpu >= 85:
            self.lbl_cpu.setStyleSheet("color: red; font-weight: bold;")
        elif isinstance(cpu, (int, float)) and cpu >= 70:
            self.lbl_cpu.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.lbl_cpu.setStyleSheet("color: green;")

        if isinstance(ram_used, (int, float)) and isinstance(ram_total, (int, float)):
            usage_percent = (ram_used / ram_total) * 100
            if usage_percent >= 85:
                self.lbl_ram.setStyleSheet("color: red; font-weight: bold;")
            elif usage_percent >= 70:
                self.lbl_ram.setStyleSheet("color: orange; font-weight: bold;")
            else:
                self.lbl_ram.setStyleSheet("color: green;")
