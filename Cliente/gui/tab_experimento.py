from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QHBoxLayout, QLineEdit, QInputDialog, QSpinBox,
    QMessageBox, QFormLayout, QProgressBar, QFrame
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from network import NetworkClient
from utils import format_duration
from gui.folder_navigator import FolderNavigator

class TabExperimento(QWidget):
    def __init__(self):
        super().__init__()
        self.client = NetworkClient()
        self.is_running = False
        self.time_left = 0
        self.server_folder = None  # Ruta relativa de la carpeta seleccionada

        self.init_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time_left)

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

        # Botones de control de experimento
        btn_layout = QHBoxLayout()
        self.btn_start = QPushButton("▶ Iniciar Experimento")
        self.btn_start.setStyleSheet("""
            QPushButton { 
                background-color: #27AE60; color: white; padding: 8px; 
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2ECC71; }
        """)
        self.btn_start.clicked.connect(self.start_experiment)

        self.btn_stop = QPushButton("⏹ Detener Experimento")
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

    def on_folder_selected(self, folder_path):
        """Manejador cuando se selecciona una carpeta en el navegador"""
        self.server_folder = folder_path
        self.path_edit.setText(folder_path)

    def create_folder_in_current(self):
        """Crea una nueva carpeta en la ubicación actual del navegador"""
        try:
            # Obtener ruta actual del navegador
            current_path = self.folder_navigator.get_current_path()
            
            folder_name, ok = QInputDialog.getText(
                self, 
                "Crear nueva carpeta", 
                "Nombre de la carpeta:"
            )
            
            if ok and folder_name.strip():
                # Construir ruta completa
                if current_path:
                    new_path = f"{current_path}/{folder_name.strip()}"
                else:
                    new_path = folder_name.strip()
                
                # Enviar al servidor
                resp = self.client.create_folder(new_path)
                
                if resp.get("status") == "success":
                    # Actualizar navegador
                    self.folder_navigator.refresh()
                    # Seleccionar nueva carpeta automáticamente
                    self.server_folder = new_path
                    self.path_edit.setText(new_path)
                    QMessageBox.information(
                        self, 
                        "Éxito", 
                        f"Carpeta creada:\n{new_path}"
                    )
                else:
                    QMessageBox.warning(
                        self, 
                        "Error", 
                        f"No se pudo crear la carpeta:\n{resp.get('message', '')}"
                    )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo crear carpeta:\n{e}")

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

        resp = self.client.start_experiment(self.server_folder, duration, interval)
        if resp.get("status") == "ok":
            self.is_running = True
            self.time_left = duration
            self.btn_start.setEnabled(False)
            self.btn_stop.setEnabled(True)
            self.timer.start(1000)
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