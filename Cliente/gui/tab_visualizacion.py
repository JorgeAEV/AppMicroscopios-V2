# gui/tab_visualizacion.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QTabWidget, QHBoxLayout
)
from PyQt6.QtCore import QTimer
from gui.tab_calibracion import TabCalibracion
from video_thread import VideoThread
from network import get_cameras
from config import BASE_URL
from system_monitor import get_cpu_usage, get_ram_usage, get_disk_space, get_temperature
from PyQt6.QtGui import QImage, QPixmap
import cv2

class TabVisualizacion(QWidget):
    def __init__(self, parent_tabs=None):
        super().__init__()
        self.parent_tabs = parent_tabs
        self.cam_threads = {}
        self.image_labels = {}
        self.init_ui()
        self.populate_camera_tabs()
        self.update_status()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(5000)

    def init_ui(self):
        self.layout = QVBoxLayout()

        self.camera_tabs = QTabWidget()
        self.layout.addWidget(self.camera_tabs)

        # Panel de estado
        self.status_layout = QHBoxLayout()
        self.cpu_label = QLabel()
        self.ram_label = QLabel()
        self.disk_label = QLabel()
        self.temp_label = QLabel()

        for label in [self.cpu_label, self.ram_label, self.disk_label, self.temp_label]:
            self.status_layout.addWidget(label)

        self.layout.addLayout(self.status_layout)

        # Botones
        self.button_layout = QHBoxLayout()
        self.btn_back = QPushButton("Regresar")
        self.btn_calibracion = QPushButton("Calibración")
        self.btn_experimento = QPushButton("Iniciar Experimento")

        self.button_layout.addWidget(self.btn_back)
        self.button_layout.addWidget(self.btn_calibracion)
        self.button_layout.addWidget(self.btn_experimento)
        self.layout.addLayout(self.button_layout)

        self.setLayout(self.layout)

        self.btn_back.clicked.connect(self.go_back)
        self.btn_calibracion.clicked.connect(self.go_calibracion)
        # Nota: aún no se implementa el experimento

    def populate_camera_tabs(self):
        cameras = get_cameras()
        for cam_id in cameras:
            label = QLabel()
            label.setFixedSize(640, 480)
            self.image_labels[cam_id] = label

            tab = QWidget()
            tab_layout = QVBoxLayout()
            tab_layout.addWidget(label)
            tab.setLayout(tab_layout)

            self.camera_tabs.addTab(tab, f"Cámara {cam_id}")

            # Iniciar hilo de video
            thread = VideoThread(f"{BASE_URL}/video_feed")
            thread.change_pixmap_signal.connect(lambda img, cid=cam_id: self.update_image(cid, img))
            thread.start()
            self.cam_threads[cam_id] = thread

    def update_image(self, cam_id, cv_img):
        if cam_id in self.image_labels:
            qt_img = self.convert_cv_qt(cv_img)
            self.image_labels[cam_id].setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(convert_to_Qt_format)

    def update_status(self):
        self.cpu_label.setText(f"CPU: {get_cpu_usage()}%")
        used, total = get_ram_usage()
        self.ram_label.setText(f"RAM: {used}/{total} MB")
        free_mb, free_gb = get_disk_space()
        self.disk_label.setText(f"Disco: {free_gb} GB ({free_mb} MB)")
        self.temp_label.setText(f"Temp: {get_temperature()} °C")

    def go_back(self):
        if self.parent_tabs:
            self.parent_tabs.setCurrentIndex(0)

    def go_calibracion(self):
        if self.parent_tabs:
            tab = TabCalibracion(parent_tabs=self.parent_tabs)
            self.parent_tabs.addTab(tab, "Calibración")
            self.parent_tabs.setCurrentWidget(tab)

    def closeEvent(self, event):
        for thread in self.cam_threads.values():
            thread.stop()
        event.accept()
