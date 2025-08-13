from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QPushButton, QHBoxLayout, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage, QFont
import cv2
import numpy as np
from video_thread import VideoThread
from network import NetworkClient
import matplotlib.pyplot as plt


class TabCalibracion(QWidget):
    def __init__(self):
        super().__init__()
        self.client = NetworkClient()
        self.current_cam_id = None  # Será seteado desde fuera o UI
        self.video_thread = None

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # === Banner de sección ===
        banner = QLabel("💡 Calibración de iluminación")
        banner.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        banner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        banner.setStyleSheet("""
            background-color: #0078D7;
            color: white;
            padding: 10px;
            border-radius: 8px;
        """)
        layout.addWidget(banner)

        # === Área de video ===
        self.image_label = QLabel("🎥 Video en vivo")
        self.image_label.setFixedSize(640, 480)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            background-color: #f0f0f0;
            border: 2px solid #cccccc;
            border-radius: 8px;
            color: #555555;
            font-size: 14px;
        """)
        layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # === Slider de brillo LED ===
        slider_layout = QHBoxLayout()
        lbl_slider = QLabel("💡 Brillo LED:")
        lbl_slider.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        slider_layout.addWidget(lbl_slider)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(0)
        self.slider.setToolTip("Intensidad LED")
        self.slider.valueChanged.connect(self.led_intensity_changed)
        self.slider.setStyleSheet("""
            QSlider::groove:horizontal {
                height: 8px;
                background: #cccccc;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #0078D7;
                border: 1px solid #005a9e;
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
        """)
        slider_layout.addWidget(self.slider)
        layout.addLayout(slider_layout)

        # === Botón de histograma ===
        self.btn_histograma = QPushButton("📊 Mostrar Histograma RGB")
        self.btn_histograma.clicked.connect(self.show_histogram)
        self.btn_histograma.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_histograma.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                padding: 8px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
        """)
        layout.addWidget(self.btn_histograma)

        layout.addStretch()
        self.setLayout(layout)

    def start_video(self, cam_id):
        self.current_cam_id = cam_id
        if self.video_thread:
            self.video_thread.stop()
        url = self.client.get_video_feed_url(cam_id)
        self.video_thread = VideoThread(url)
        self.video_thread.frame_received.connect(self.update_image)
        self.video_thread.start()

        # Encender LED para calibración al iniciar
        self.client.led_control(cam_id, 'on')

    def stop_video(self):
        if self.video_thread:
            self.video_thread.stop()
            self.video_thread = None
        # Apagar LED al salir
        if self.current_cam_id is not None:
            self.client.led_control(self.current_cam_id, 'off')

    def update_image(self, cv_img):
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_img = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_img).scaled(self.image_label.width(), self.image_label.height(), Qt.AspectRatioMode.KeepAspectRatio)
        self.image_label.setPixmap(pixmap)

    def led_intensity_changed(self, value):
        # Aquí se podría implementar control PWM si el servidor lo soporta
        print(f"Intensidad LED cambiada a {value}% (no implementado en servidor)")

    def show_histogram(self):
        if not self.video_thread:
            QMessageBox.warning(self, "⚠️ Advertencia", "No hay video activo para analizar")
            return
        try:
            pixmap = self.image_label.pixmap()
            if pixmap is None:
                raise Exception("No hay imagen disponible")
            img = pixmap.toImage()
            ptr = img.bits()
            ptr.setsize(img.byteCount())
            arr = np.array(ptr).reshape(img.height(), img.width(), 4)
            img_rgb = cv2.cvtColor(arr, cv2.COLOR_RGBA2RGB)

            # Histogramas
            color = ('r', 'g', 'b')
            plt.figure("Histograma RGB")
            for i, col in enumerate(color):
                hist = cv2.calcHist([img_rgb], [i], None, [256], [0, 256])
                plt.plot(hist, color=col)
                plt.xlim([0, 256])
            plt.title("Histograma RGB")
            plt.show()
        except Exception as e:
            QMessageBox.warning(self, "❌ Error", f"No se pudo generar histograma: {e}")
