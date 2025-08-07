# gui/main_window.py
from PyQt6.QtWidgets import QMainWindow, QTabWidget
from gui.tab_bienvenida import TabBienvenida
from gui.tab_visualizacion import TabVisualizacion
from gui.tab_experimento import TabExperimento

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cliente - Microscopios Raspberry Pi")
        self.resize(1000, 700)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Instanciar pestañas
        self.tab_bienvenida = TabBienvenida()
        self.tab_visualizacion = TabVisualizacion(parent_tabs=self.tabs)
        self.tab_experimento = TabExperimento(parent_tabs=self.tabs)

        # Agregar al widget
        self.tabs.addTab(self.tab_bienvenida, "Inicio")
        self.tabs.addTab(self.tab_visualizacion, "Cámaras")
        self.tabs.addTab(self.tab_experimento, "Experimento")
