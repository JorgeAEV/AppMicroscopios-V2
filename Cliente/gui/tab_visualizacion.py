from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage
import cv2
import numpy as np
from video_thread import VideoThread
from network import NetworkClient
from system_monitor import SystemMonitor

class TabVisualizacion(QWidget):
    def __init__(self):
        super().__init__()
        self.client = NetworkClient()
        self.system_monitor = SystemMonitor()

        self.video_threads = {}  # cam_id -> VideoThread

        self.init_ui()
        self.load_cameras()
        self.system_monitor.status_updated.connect(self.update_status)

    def init_ui(self):
        layout = QVBoxLayout()

        self.tabs_cams = QTabWidget()
        layout.addWidget(self.tabs_cams)

        # Botones arriba
        btn_layout = QHBoxLayout()
        self.btn_regresar = QPushButton("Regresar")
        self.btn_calibracion = QPushButton("Calibración")
        self.btn_iniciar = QPushButton("Iniciar Experimento")

        btn_layout.addWidget(self.btn_regresar)
        btn_layout.addWidget(self.btn_calibracion)
        btn_layout.addWidget(self.btn_iniciar)
        layout.addLayout(btn_layout)

        # Panel de estado
        self.lbl_temp = QLabel("Temperatura CPU: - °C")
        self.lbl_cpu = QLabel("CPU Uso: - %")
        self.lbl_ram = QLabel("RAM Usada: - MB / - MB")
        self.lbl_disk = QLabel("Almacenamiento Libre: - GB")

        estado_layout = QVBoxLayout()
        estado_layout.addWidget(self.lbl_temp)
        estado_layout.addWidget(self.lbl_cpu)
        estado_layout.addWidget(self.lbl_ram)
        estado_layout.addWidget(self.lbl_disk)

        layout.addLayout(estado_layout)

        self.setLayout(layout)

    def load_cameras(self):
        cameras = self.client.get_cameras()
        self.tabs_cams.clear()
        self.stop_all_videos()

        for cam_id in cameras:
            tab = QWidget()
            tab_layout = QVBoxLayout()

            lbl_video = QLabel()
            lbl_video.setFixedSize(640, 480)
            tab_layout.addWidget(lbl_video)

            tab.setLayout(tab_layout)
            self.tabs_cams.addTab(tab, f"Microscopio {cam_id}")

            # Iniciar hilo de video
            url = self.client.get_video_feed_url(cam_id)
            video_thread = VideoThread(url)
            video_thread.frame_received.connect(lambda img, lbl=lbl_video: self.update_image(lbl, img))
            video_thread.start()

            self.video_threads[cam_id] = video_thread

    def stop_all_videos(self):
        for thread in self.video_threads.values():
            thread.stop()
        self.video_threads.clear()

    def update_image(self, label, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img).scaled(label.width(), label.height(), Qt.AspectRatioMode.KeepAspectRatio)
        label.setPixmap(pixmap)

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
