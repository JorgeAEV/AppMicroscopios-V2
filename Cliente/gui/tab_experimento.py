from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QLineEdit, QInputDialog, QSpinBox,
    QMessageBox, QFormLayout, QProgressBar, QFrame,
    QGroupBox, QCheckBox, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QIcon
from network import NetworkClient
from utils import format_duration
from gui.folder_navigator import FolderNavigator
import re


class TabExperimento(QWidget):
    def __init__(self):
        super().__init__()
        self.client = NetworkClient()
        self.is_running = False
        self.time_left = 0
        self.server_folder = None  # Ruta relativa de la carpeta seleccionada

        # Cámaras detectadas y checkboxes
        self.cameras = []
        self.checkboxes = []
        self.chk_all = None

        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_left)

        # Cargar listado de cámaras
        self.load_cameras()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Título
        title = QLabel("🧪 Control de Experimentos")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        # Navegador de carpetas
        layout.addWidget(QLabel("Navegador de Carpetas:"))
        self.folder_navigator = FolderNavigator(self.client)
        self.folder_navigator.folder_selected.connect(self.on_folder_selected)
        layout.addWidget(self.folder_navigator)

        # Ruta seleccionada
        layout.addWidget(QLabel("Carpeta seleccionada para el experimento:"))
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setStyleSheet("background-color: #f0f0f0; padding: 6px; border-radius: 4px;")
        layout.addWidget(self.path_edit)

        # Botón para crear carpeta
        self.btn_create = QPushButton("📂 Crear nueva carpeta aquí")
        self.btn_create.setStyleSheet("""
            QPushButton { 
                background-color: #16A085; color: white; padding: 6px; 
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #1ABC9C; }
        """)
        self.btn_create.clicked.connect(self.create_folder_in_current)
        layout.addWidget(self.btn_create)

        # Formulario
        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        # Duración
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(1, 14400)
        self.duration_spin.setValue(300)
        self.duration_spin.setSuffix(" seg")
        form_layout.addRow("Duración total:", self.duration_spin)

        # Intervalo
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 3600)
        self.interval_spin.setValue(60)
        self.interval_spin.setSuffix(" seg")
        form_layout.addRow("Intervalo entre capturas:", self.interval_spin)

        layout.addLayout(form_layout)

        # === Selección de cámaras ===
        grp = QGroupBox("Cámaras para el experimento")
        vgrp = QVBoxLayout(grp)

        self.chk_all = QCheckBox("Seleccionar todas")
        self.chk_all.setChecked(True)
        self.chk_all.stateChanged.connect(self.toggle_all)
        vgrp.addWidget(self.chk_all)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll.setWidget(self.scroll_widget)
        vgrp.addWidget(self.scroll)

        layout.addWidget(grp)

        # Botones de control de experimento
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶ Iniciar Experimento")
        self.btn_start.setIcon(QIcon(":/icons/start.png"))
        self.btn_start.setStyleSheet("""
            QPushButton { 
                background-color: #27AE60; color: white; padding: 8px; 
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2ECC71; }
        """)
        self.btn_start.clicked.connect(self.start_experiment)

        self.btn_stop = QPushButton("⏹ Detener Experimento")
        self.btn_stop.setIcon(QIcon(":/icons/stop.png"))
        self.btn_stop.setStyleSheet("""
            QPushButton { 
                background-color: #C0392B; color: white; padding: 8px; 
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #E74C3C; }
        """)
        self.btn_stop.clicked.connect(self.stop_experiment)
        self.btn_stop.setEnabled(False)

        btn_layout.addWidget(self.btn_start)
        btn_layout.addWidget(self.btn_stop)
        layout.addLayout(btn_layout)

        # Tiempo restante
        self.lbl_time_left = QLabel("Tiempo restante: --:--:--")
        self.lbl_time_left.setFont(QFont("Consolas", 14))
        self.lbl_time_left.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_time_left)

        # Barra de progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar { 
                border: 1px solid #aaa; border-radius: 6px; 
                text-align: center; height: 22px; 
            }
            QProgressBar::chunk { 
                background-color: #27AE60; border-radius: 6px; 
            }
        """)
        layout.addWidget(self.progress_bar)

        layout.addStretch()
        self.setLayout(layout)

    # ------------------------------
    #   Manejo de carpetas
    # ------------------------------
    def on_folder_selected(self, folder_path):
        self.server_folder = folder_path
        self.path_edit.setText(folder_path)

    def create_folder_in_current(self):
        try:
            current_path = self.folder_navigator.get_current_path()
            folder_name, ok = QInputDialog.getText(
                self,
                "Crear nueva carpeta",
                "Nombre de la carpeta (solo letras, números y guiones bajos):"
            )
            if ok and folder_name.strip():
                if not self.is_valid_folder_name(folder_name.strip()):
                    QMessageBox.warning(
                        self,
                        "Nombre inválido",
                        "Solo se permiten letras, números y guiones bajos. "
                        "No se permiten espacios, caracteres especiales ni barras."
                    )
                    return
                if current_path:
                    new_path = f"{current_path}/{folder_name.strip()}"
                else:
                    new_path = folder_name.strip()
                resp = self.client.create_folder(new_path)
                if resp.get("status") == "success":
                    self.folder_navigator.current_path = new_path
                    self.folder_navigator.refresh()
                    self.on_folder_selected(new_path)
                    QMessageBox.information(self, "Éxito", f"Carpeta creada:\n{new_path}")
                else:
                    QMessageBox.warning(self, "Error", f"No se pudo crear la carpeta:\n{resp.get('message', '')}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear carpeta:\n{e}")

    def is_valid_folder_name(self, name):
        return bool(re.match(r'^[a-zA-Z0-9_]+$', name))

    # ------------------------------
    #   Selección de cámaras
    # ------------------------------
    def load_cameras(self):
        self.cameras = self.client.get_cameras()
        # Limpia scroll
        for i in reversed(range(self.scroll_layout.count())):
            w = self.scroll_layout.itemAt(i).widget()
            if w:
                w.setParent(None)
        self.checkboxes = []
        for cam_id in self.cameras:
            cb = QCheckBox(f"Cámara {cam_id}")
            cb.setChecked(True)
            cb.stateChanged.connect(self.on_any_cam_changed)
            self.checkboxes.append((cam_id, cb))
            self.scroll_layout.addWidget(cb)
        self.scroll_layout.addStretch()

    def toggle_all(self, _state):
        checked = self.chk_all.isChecked()
        for _, cb in self.checkboxes:
            cb.blockSignals(True)
            cb.setChecked(checked)
            cb.blockSignals(False)

    def on_any_cam_changed(self, _state):
        all_checked = all(cb.isChecked() for _, cb in self.checkboxes)
        self.chk_all.blockSignals(True)
        self.chk_all.setChecked(all_checked)
        self.chk_all.blockSignals(False)

    def selected_camera_ids(self):
        if self.chk_all.isChecked():
            return None  # todas
        selected = [cam_id for cam_id, cb in self.checkboxes if cb.isChecked()]
        return selected if selected else None

    # ------------------------------
    #   Control de experimento
    # ------------------------------
    def start_experiment(self):
        if self.is_running:
            return
        if not self.server_folder:
            QMessageBox.warning(self, "Error", "Debe seleccionar una carpeta para el experimento")
            return
        duration = self.duration_spin.value()
        interval = self.interval_spin.value()
        if interval > duration:
            QMessageBox.warning(self, "Error", "El intervalo no puede ser mayor que la duración")
            return

        sanitized_path = self.server_folder.replace("\\", "/")
        cam_ids = self.selected_camera_ids()

        resp = self.client.start_experiment(sanitized_path, duration, interval, camera_ids=cam_ids)
        if resp.get("status") == "ok":
            self.is_running = True
            self.time_left = duration
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.timer.start(1000)
            used = resp.get("camera_ids", cam_ids or "todas")
            QMessageBox.information(self, "Experimento iniciado", f"Cámaras utilizadas: {used}")
        else:
            QMessageBox.critical(self, "Error", f"No se pudo iniciar experimento:\n{resp.get('message', '')}")

    def stop_experiment(self):
        if not self.is_running:
            return
        resp = self.client.stop_experiment()
        if resp.get("status") == "ok":
            self.is_running = False
            self.timer.stop()
            self.time_left = 0
            self.btn_start.setEnabled(True)
            self.btn_stop.setEnabled(False)
            self.lbl_time_left.setText("Tiempo restante: --:--:--")
            self.progress_bar.setValue(0)
            self.folder_navigator.refresh()
        else:
            QMessageBox.critical(self, "Error", f"No se pudo detener experimento:\n{resp.get('message', '')}")

    def update_time_left(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.lbl_time_left.setText(f"Tiempo restante: {format_duration(self.time_left)}")
            total = self.duration_spin.value()
            self.progress_bar.setValue(int(100 * (total - self.time_left) / total))
        else:
            self.stop_experiment()
