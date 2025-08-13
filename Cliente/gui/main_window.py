from PyQt6.QtWidgets import QMainWindow, QTabWidget
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt

from gui.tab_bienvenida import TabBienvenida
from gui.tab_visualizacion import TabVisualizacion
from gui.tab_calibracion import TabCalibracion
from gui.tab_experimento import TabExperimento


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BioScope - Cliente Microscopios Raspberry Pi")
        self.resize(1100, 750)
        self.setWindowIcon(QIcon("assets/icon.png"))

        # Contenedor de pestañas
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setMovable(False)
        self.tabs.setDocumentMode(True)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #2980B9;
                background-color: #FDFEFE;
                border-radius: 6px;
            }
            QTabBar::tab {
                background: #D6EAF8;
                padding: 8px 20px;
                border-radius: 4px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #3498DB;
                color: white;
            }
        """)
        self.setCentralWidget(self.tabs)

        # Pestañas
        self.tab_bienvenida = TabBienvenida()
        self.tab_visualizacion = TabVisualizacion()
        self.tab_calibracion = TabCalibracion()
        self.tab_experimento = TabExperimento()

        self.tabs.addTab(self.tab_bienvenida, "Bienvenida")
        self.tabs.addTab(self.tab_visualizacion, "Visualización")
        self.tabs.addTab(self.tab_calibracion, "Calibración")
        self.tabs.addTab(self.tab_experimento, "Experimento")

        # Conexiones de botones
        self.tab_visualizacion.btn_regresar.clicked.connect(self.goto_bienvenida)
        self.tab_visualizacion.btn_calibracion.clicked.connect(self.goto_calibracion)
        self.tab_visualizacion.btn_iniciar.clicked.connect(self.goto_experimento)

        self.tab_calibracion.slider.valueChanged.connect(self.handle_led_intensity_change)

        self.tabs.currentChanged.connect(self.on_tab_changed)

    def goto_bienvenida(self):
        self.tabs.setCurrentWidget(self.tab_bienvenida)

    def goto_calibracion(self):
        current_cam_index = self.get_current_camera_id()
        if current_cam_index is None:
            return
        self.tab_calibracion.start_video(current_cam_index)
        self.tabs.setCurrentWidget(self.tab_calibracion)

    def goto_experimento(self):
        self.tabs.setCurrentWidget(self.tab_experimento)

    def on_tab_changed(self, index):
        widget = self.tabs.widget(index)
        if widget != self.tab_calibracion:
            self.tab_calibracion.stop_video()

    def get_current_camera_id(self):
        current_index = self.tab_visualizacion.tabs_cams.currentIndex()
        if current_index == -1:
            return None
        cam_text = self.tab_visualizacion.tabs_cams.tabText(current_index)
        try:
            cam_id = int(cam_text.split()[-1])
            return cam_id
        except Exception:
            return None

    def handle_led_intensity_change(self, value):
        # Futuro: enviar valor al servidor
        pass
