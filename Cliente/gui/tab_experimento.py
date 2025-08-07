# gui/tab_experimento.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton,
    QFileDialog, QLineEdit, QHBoxLayout
)
from PyQt6.QtCore import QTimer
from network import start_experiment, stop_experiment

class TabExperimento(QWidget):
    def __init__(self, parent_tabs=None):
        super().__init__()
        self.parent_tabs = parent_tabs
        self.remaining_time = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        self.experiment_active = False

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.path_label = QLabel("Ruta de guardado:")
        layout.addWidget(self.path_label)

        path_layout = QHBoxLayout()
        self.path_input = QLineEdit()
        self.browse_btn = QPushButton("Seleccionar carpeta")
        self.browse_btn.clicked.connect(self.select_folder)
        path_layout.addWidget(self.path_input)
        path_layout.addWidget(self.browse_btn)
        layout.addLayout(path_layout)

        self.duration_label = QLabel("Duración (minutos):")
        self.duration_input = QLineEdit()
        layout.addWidget(self.duration_label)
        layout.addWidget(self.duration_input)

        self.interval_label = QLabel("Intervalo de captura (segundos):")
        self.interval_input = QLineEdit()
        layout.addWidget(self.interval_label)
        layout.addWidget(self.interval_input)

        self.start_btn = QPushButton("Iniciar experimento")
        self.start_btn.clicked.connect(self.start_experiment)
        layout.addWidget(self.start_btn)

        self.timer_label = QLabel("Tiempo restante: --:--")
        layout.addWidget(self.timer_label)

        self.cancel_btn = QPushButton("Cancelar experimento")
        self.cancel_btn.clicked.connect(self.cancel_experiment)
        self.cancel_btn.setEnabled(False)
        layout.addWidget(self.cancel_btn)

        self.setLayout(layout)

    def select_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta")
        if path:
            self.path_input.setText(path)

    def start_experiment(self):
        path = self.path_input.text()
        try:
            duration_min = int(self.duration_input.text())
            interval_sec = int(self.interval_input.text())
        except ValueError:
            self.timer_label.setText("Error: Valores inválidos")
            return

        duration_sec = duration_min * 60
        self.remaining_time = duration_sec

        try:
            resp = start_experiment(path, duration_sec, interval_sec)
            if resp.status_code == 200:
                self.experiment_active = True
                self.cancel_btn.setEnabled(True)
                self.start_btn.setEnabled(False)
                self.timer.start(1000)
                self.timer_label.setText(f"Tiempo restante: {self.remaining_time} s")
                # Desactivar otras pestañas
                if self.parent_tabs:
                    for i in range(self.parent_tabs.count()):
                        if self.parent_tabs.widget(i) != self:
                            self.parent_tabs.setTabEnabled(i, False)
            else:
                self.timer_label.setText("Error al iniciar experimento")
        except Exception as e:
            self.timer_label.setText(f"Error: {e}")

    def update_timer(self):
        if self.remaining_time > 0:
            self.remaining_time -= 1
            mins = self.remaining_time // 60
            secs = self.remaining_time % 60
            self.timer_label.setText(f"Tiempo restante: {mins:02}:{secs:02}")
        else:
            self.finish_experiment()

    def cancel_experiment(self):
        stop_experiment()
        self.finish_experiment()

    def finish_experiment(self):
        self.timer.stop()
        self.timer_label.setText("Experimento finalizado o cancelado.")
        self.cancel_btn.setEnabled(False)
        self.start_btn.setEnabled(True)
        self.experiment_active = False

        # Reactivar pestañas
        if self.parent_tabs:
            for i in range(self.parent_tabs.count()):
                self.parent_tabs.setTabEnabled(i, True)
