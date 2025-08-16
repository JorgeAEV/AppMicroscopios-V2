from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton, 
    QHBoxLayout, QLabel, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import os

class FolderNavigator(QWidget):
    folder_selected = pyqtSignal(str)  # Señal cuando se selecciona una carpeta
    
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.current_path = ""  # Ruta relativa actual
        self.init_ui()
        self.refresh()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra de navegación
        nav_layout = QHBoxLayout()
        self.btn_up = QPushButton("↑ Subir")
        self.btn_up.setFont(QFont("Arial", 10))
        self.btn_up.clicked.connect(self.navigate_up)
        self.lbl_path = QLabel("Raíz")
        self.lbl_path.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        nav_layout.addWidget(self.btn_up)
        nav_layout.addWidget(self.lbl_path)
        nav_layout.addStretch()
        layout.addLayout(nav_layout)
        
        # Lista de carpetas
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont("Arial", 11))
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)
        
        self.setLayout(layout)
    
    def refresh(self):
        """Actualiza la vista del directorio actual"""
        try:
            data = self.client.list_directory(self.current_path)
            self.list_widget.clear()
            
            # Mostrar carpeta padre si no estamos en raíz
            if self.current_path:
                item = QListWidgetItem(".. (directorio padre)")
                item.setData(Qt.ItemDataRole.UserRole, os.path.dirname(self.current_path))
                self.list_widget.addItem(item)
            
            # Mostrar carpetas
            for folder in data.get("folders", []):
                item = QListWidgetItem(f"📁 {folder}")
                item.setData(Qt.ItemDataRole.UserRole, os.path.join(self.current_path, folder))
                self.list_widget.addItem(item)
            
            # Actualizar barra de ruta
            display_path = self.current_path if self.current_path else "/ (raíz)"
            self.lbl_path.setText(display_path)
            
            # Habilitar/deshabilitar botón de subir
            self.btn_up.setEnabled(bool(self.current_path))
            
        except Exception as e:
            # En una aplicación real, mostrarías un mensaje de error
            print(f"Error al refrescar: {e}")
    
    def navigate_up(self):
        """Navega al directorio padre"""
        if not self.current_path:
            return
        
        parent_path = os.path.dirname(self.current_path)
        self.current_path = parent_path
        self.refresh()
    
    def on_item_double_clicked(self, item):
        """Maneja el doble clic en un item de la lista"""
        new_path = item.data(Qt.ItemDataRole.UserRole)
        
        # Si es ".." o una carpeta, navegamos
        if item.text().startswith("..") or item.text().startswith("📁"):
            self.current_path = new_path
            self.refresh()
        else:
            # Emitir señal de carpeta seleccionada
            self.folder_selected.emit(new_path)
    
    def get_current_path(self):
        """Devuelve la ruta relativa actual"""
        return self.current_path