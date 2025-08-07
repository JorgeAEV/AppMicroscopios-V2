# gui/tab_bienvenida.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton
from PyQt6.QtCore import QTimer
from network import get_cameras
from system_monitor import get_cpu_usage, get_ram_usage, get_disk_space, get_temperature

class TabBienvenida(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.update_info()

        # Refrescar estado del sistema cada 5 segundos
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_info)
        self.timer.start(5000)

    def init_ui(self):
        layout = QVBoxLayout()

        self.label_title = QLabel("<h2>Bienvenido al cliente de monitoreo de microscopios</h2>")
        layout.addWidget(self.label_title)

        self.label_cams = QLabel("Cámaras conectadas:")
        layout.addWidget(self.label_cams)

        self.cam_list = QListWidget()
        layout.addWidget(self.cam_list)

        self.refresh_btn = QPushButton("Actualizar cámaras")
        self.refresh_btn.clicked.connect(self.load_cameras)
        layout.addWidget(self.refresh_btn)

        self.status_title = QLabel("<h3>Estado del sistema (Raspberry Pi)</h3>")
        layout.addWidget(self.status_title)

        self.cpu_label = QLabel("CPU: ")
        self.ram_label = QLabel("RAM: ")
        self.disk_label = QLabel("Almacenamiento: ")
        self.temp_label = QLabel("Temperatura: ")

        layout.addWidget(self.cpu_label)
        layout.addWidget(self.ram_label)
        layout.addWidget(self.disk_label)
        layout.addWidget(self.temp_label)

        self.setLayout(layout)

    def load_cameras(self):
        try:
            cameras = get_cameras()
            self.cam_list.clear()
            for cam in cameras:
                self.cam_list.addItem(f"Cámara {cam}")
        except Exception as e:
            self.cam_list.clear()
            self.cam_list.addItem("Error al obtener cámaras.")
            print(f"Error: {e}")

    def update_info(self):
        self.load_cameras()

        cpu = get_cpu_usage()
        used_ram, total_ram = get_ram_usage()
        free_mb, free_gb = get_disk_space()
        temp = get_temperature()

        self.cpu_label.setText(f"CPU: {cpu}%")
        self.ram_label.setText(f"RAM: {used_ram} MB / {total_ram} MB")
        self.disk_label.setText(f"Almacenamiento libre: {free_gb} GB ({free_mb} MB)")
        self.temp_label.setText(f"Temperatura CPU: {temp} °C")
