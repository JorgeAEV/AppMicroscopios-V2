from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel, QPushButton, QHBoxLayout, QFrame, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage, QFont, QColor, QPalette
import cv2
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

        # Título principal
        title = QLabel("🔬 Visualización en Tiempo Real")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2E86C1; margin-bottom: 15px;")
        layout.addWidget(title)

        # Tabs de cámaras
        self.tabs_cams = QTabWidget()
        self.tabs_cams.setStyleSheet("""
            QTabWidget::pane { border: 2px solid #3498DB; border-radius: 6px; }
            QTabBar::tab {
                background: #D6EAF8;
                border: 1px solid #3498DB;
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QTabBar::tab:selected {
                background: #3498DB;
                color: white;
            }
        """)
        layout.addWidget(self.tabs_cams)

        # Botones
        btn_layout = QHBoxLayout()
        self.btn_regresar = QPushButton("⬅️ Regresar")
        self.btn_calibracion = QPushButton("🛠️ Calibración")
        self.btn_iniciar = QPushButton("▶️ Iniciar Experimento")

        for btn in [self.btn_regresar, self.btn_calibracion, self.btn_iniciar]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    font-weight: bold;
                    padding: 6px 12px;
                    border-radius: 6px;
                }
                QPushButton:hover {
                    background-color: #2E86C1;
                }
            """)
            btn_layout.addWidget(btn)

        layout.addLayout(btn_layout)

        # Estado Raspberry Pi
        estado_group = QGroupBox("📊 Estado Raspberry Pi")
        estado_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #2E86C1;
                border-radius: 8px;
                margin-top: 10px;
            }
        """)
        estado_layout = QVBoxLayout()

        self.lbl_temp = QLabel("🌡️ Temperatura CPU: - °C")
        self.lbl_cpu = QLabel("⚙️ CPU Uso: - %")
        self.lbl_ram = QLabel("🧠 RAM Usada: - MB / - MB")
        self.lbl_disk = QLabel("💾 Almacenamiento Libre: - GB")

        for lbl in [self.lbl_temp, self.lbl_cpu, self.lbl_ram, self.lbl_disk]:
            lbl.setFont(QFont("Segoe UI", 10))
            estado_layout.addWidget(lbl)

        estado_group.setLayout(estado_layout)
        layout.addWidget(estado_group)

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
            lbl_video.setStyleSheet("background-color: black; border: 2px solid #3498DB;")
            tab_layout.addWidget(lbl_video, alignment=Qt.AlignmentFlag.AlignCenter)

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

        # Colores de advertencia
        def colorize(value, warn, danger):
            if value == "-":
                return "black"
            try:
                v = float(value)
                if v >= danger:
                    return "red"
                elif v >= warn:
                    return "orange"
                else:
                    return "green"
            except:
                return "black"

        self.lbl_temp.setText(f"🌡️ Temperatura CPU: {temp} °C")
        self.lbl_temp.setStyleSheet(f"color: {colorize(temp, 65, 80)};")

        self.lbl_cpu.setText(f"⚙️ CPU Uso: {cpu} %")
        self.lbl_cpu.setStyleSheet(f"color: {colorize(cpu, 60, 85)};")

        self.lbl_ram.setText(f"🧠 RAM Usada: {ram_used} MB / {ram_total} MB")
        if ram_used != "-" and ram_total != "-":
            ram_percent = (float(ram_used) / float(ram_total)) * 100
            self.lbl_ram.setStyleSheet(f"color: {colorize(ram_percent, 60, 85)};")

        self.lbl_disk.setText(f"💾 Almacenamiento Libre: {disk_free} GB")
        self.lbl_disk.setStyleSheet(f"color: {colorize(disk_free, 10, 5)};")
