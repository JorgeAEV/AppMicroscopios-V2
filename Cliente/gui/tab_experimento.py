from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QLineEdit, QInputDialog, QSpinBox,
    QMessageBox, QFormLayout, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from network import NetworkClient
from utils import format_duration
import os


class TabExperimento(QWidget):
    def __init__(self):
        super().__init__()
        self.client = NetworkClient()
        self.is_running = False
        self.time_left = 0
        self.server_folder = None

        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_left)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)

        title = QLabel("▶ Control de Experimentos")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        btn_select = QPushButton("📁 Elegir carpeta (Servidor)")
        btn_select.clicked.connect(self.select_server_folder)
        btn_select.setStyleSheet("background-color: #2980B9; color: white; padding: 6px; border-radius: 4px;")

        path_layout = QHBoxLayout()
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(btn_select)
        form_layout.addRow("Carpeta en servidor:", path_layout)

        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 14400)
        self.duration_spin.setValue(300)
        self.duration_spin.setSuffix(" seg")
        form_layout.addRow("Duración total:", self.duration_spin)

        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 3600)
        self.interval_spin.setValue(60)
        self.interval_spin.setSuffix(" seg")
        form_layout.addRow("Intervalo entre capturas:", self.interval_spin)

        layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶ Iniciar Experimento")
        self.btn_start.setStyleSheet("background-color: #27AE60; color: white; padding: 8px; border-radius: 6px;")
        self.btn_start.clicked.connect(self.start_experiment)

        self.btn_stop = QPushButton("⏹ Detener Experimento")
        self.btn_stop.setStyleSheet("background-color: #C0392B; color: white; padding: 8px; border-radius: 6px;")
        self.btn_stop.clicked.connect(self.stop_experiment)
        self.btn_stop.setEnabled(False)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        layout.addLayout(btn_layout)

        self.lbl_time_left = QLabel("Tiempo restante: --:--:--")
        self.lbl_time_left.setFont(QFont("Consolas", 12))
        self.lbl_time_left.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_time_left)

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        layout.addStretch()
        self.setLayout(layout)

    def select_server_folder(self):
        try:
            folders = self.client.list_folders()
            folder, ok = QInputDialog.getItem(
                self, "Seleccionar carpeta en servidor",
                "Carpetas existentes:", folders, editable=True
            )
            if ok and folder:
                resp = self.client.create_folder(folder)
                if 'path' in resp:
                    self.server_folder = resp['path']
                    self.path_edit.setText(self.server_folder)
                else:
                    QMessageBox.warning(self, "Error", "No se pudo crear la carpeta en el servidor.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo obtener carpetas del servidor:\n{e}")

    def start_experiment(self):
        if self.is_running:
            return
        if not self.server_folder:
            QMessageBox.warning(self, "Error", "Debe seleccionar una carpeta válida en el servidor.")
            return
        duration = self.duration_spin.value()
        interval = self.interval_spin.value()
        if interval > duration:
            QMessageBox.warning(self, "Error", "El intervalo no puede ser mayor que la duración.")
            return
        resp = self.client.start_experiment(self.server_folder, duration, interval)
        if resp.get('status') == 'ok':
            self.is_running = True
            self.time_left = duration
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.timer.start(1000)
        else:
            QMessageBox.critical(self, "Error", f"No se pudo iniciar experimento:\n{resp.get('message')}")

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
            QMessageBox.critical(self, "Error", f"No se pudo detener experimento:\n{resp.get('message')}")

    def update_time_left(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.lbl_time_left.setText(f"Tiempo restante: {format_duration(self.time_left)}")
            total = self.duration_spin.value()
            self.progress_bar.setValue(int(100 * (total - self.time_left) / total))
        else:
            self.stop_experiment()
