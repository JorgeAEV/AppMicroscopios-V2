# gui/tab_calibracion.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QSlider, QFileDialog
)
from PyQt6.QtCore import Qt
from video_thread import VideoThread
from config import BASE_URL
from utils import generate_rgb_histogram
import cv2
from PyQt6.QtGui import QImage, QPixmap

class TabCalibracion(QWidget):
    def __init__(self, parent_tabs=None):
        super().__init__()
        self.parent_tabs = parent_tabs
        self.video_thread = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.label_video = QLabel()
        self.label_video.setFixedSize(640, 480)
        layout.addWidget(self.label_video)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 255)
        self.slider.setValue(128)
        layout.addWidget(QLabel("Brillo LED (simulado):"))
        layout.addWidget(self.slider)

        self.histogram_btn = QPushButton("Generar histograma RGB de imagen de prueba")
        layout.addWidget(self.histogram_btn)

        self.btn_back = QPushButton("Regresar")
        layout.addWidget(self.btn_back)

        self.setLayout(layout)

        self.histogram_btn.clicked.connect(self.load_image_for_histogram)
        self.btn_back.clicked.connect(self.go_back)

        self.start_video()

    def start_video(self):
        self.video_thread = VideoThread(f"{BASE_URL}/video_feed")
        self.video_thread.change_pixmap_signal.connect(self.update_image)
        self.video_thread.start()

    def update_image(self, cv_img):
        qt_img = self.convert_cv_qt(cv_img)
        self.label_video.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        return QPixmap.fromImage(convert_to_Qt_format)

    def load_image_for_histogram(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen")
        if file_path:
            generate_rgb_histogram(file_path)

    def go_back(self):
        if self.parent_tabs:
            self.parent_tabs.setCurrentIndex(1)

    def closeEvent(self, event):
        if self.video_thread:
            self.video_thread.stop()
        event.accept()
