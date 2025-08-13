from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QLineEdit, 
    QFileDialog, QSpinBox, QMessageBox, QFormLayout, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette
from network import NetworkClient
from utils import format_duration
import os
import time


class TabExperimento(QWidget):
    def __init__(self):
        super().__init__()
        self.client = NetworkClient()
        self.is_running = False
        self.time_left = 0

        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_left)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)

        # Título
        title_label = QLabel("Control de Experimento")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        # Línea separadora
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.path_edit = QLineEdit()
        self.btn_browse = QPushButton("📁 Seleccionar carpeta")
        self.btn_browse.clicked.connect(self.browse_folder)

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.btn_browse)
        form_layout.addRow("Ruta para guardar imágenes:", path_layout)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 14400)  # 1 seg a 4 horas
        self.duration_spin.setValue(300)
        self.duration_spin.setSuffix(" seg")
        form_layout.addRow("Duración total:", self.duration_spin)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 3600)  # 1 seg a 1 hora
        self.interval_spin.setValue(60)
        self.interval_spin.setSuffix(" seg")
        form_layout.addRow("Intervalo entre capturas:", self.interval_spin)

        main_layout.addLayout(form_layout)

        # Botones de control
        buttons_layout = QHBoxLayout()

        self.btn_start = QPushButton("▶ Iniciar Experimento")
        self.btn_start.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.btn_start.clicked.connect(self.start_experiment)

        self.btn_stop = QPushButton("⏹ Detener Experimento")
        self.btn_stop.setStyleSheet("background-color: #E53935; color: white; font-weight: bold;")
        self.btn_stop.clicked.connect(self.stop_experiment)
        self.btn_stop.setEnabled(False)

        buttons_layout.addWidget(self.btn_start)
        buttons_layout.addWidget(self.btn_stop)
        main_layout.addLayout(buttons_layout)

        # Estado y progreso
        self.lbl_time_left = QLabel("Tiempo restante: --:--:--")
        self.lbl_time_left.setFont(QFont("Consolas", 12))
        self.lbl_time_left.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.lbl_time_left)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        main_layout.addWidget(self.progress_bar)

        main_layout.addStretch()
        self.setLayout(main_layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta para guardar imágenes")
        if folder:
            self.path_edit.setText(folder)

    def start_experiment(self):
        if self.is_running:
            return
        path = self.path_edit.text().strip()
        if not path or not os.path.isdir(path):
            QMessageBox.warning(self, "Error", "Debe seleccionar una carpeta válida")
            return
        duration = self.duration_spin.value()
        interval = self.interval_spin.value()
        if interval > duration:
            QMessageBox.warning(self, "Error", "El intervalo no puede ser mayor que la duración")
            return
        resp = self.client.start_experiment(path, duration, interval)
        if resp.get('status') == 'ok':
            self.is_running = True
            self.time_left = duration
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.timer.start(1000)
        else:
            QMessageBox.critical(self, "Error", f"No se pudo iniciar experimento: {resp.get('message')}")

    def stop_experiment(self):
        if not self.is_running:
            return
        resp = self.client.stop_experiment()
        if resp.get('status') == 'ok':
            self.is_running = False
            self.timer.stop()
            self.time_left = 0
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.lbl_time_left.setText("Tiempo restante: --:--:--")
            self.progress_bar.setValue(0)
        else:
            QMessageBox.critical(self, "Error", f"No se pudo detener experimento: {resp.get('message')}")

    def update_time_left(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.lbl_time_left.setText(f"Tiempo restante: {format_duration(self.time_left)}")
            total = self.duration_spin.value()
            self.progress_bar.setValue(100 * (total - self.time_left) / total)
        else:
            self.stop_experiment()
