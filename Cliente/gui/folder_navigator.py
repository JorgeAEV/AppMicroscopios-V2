from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton, 
    QHBoxLayout, QLabel, QListWidgetItem
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QBrush, QColor
import os
import re

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
        self.btn_up.setEnabled(False)
        
        self.lbl_path = QLabel("Raíz")
        self.lbl_path.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.lbl_path.setStyleSheet("padding: 4px; background-color: #f0f0f0; border-radius: 4px;")
        
        # Botón de refrescar
        self.btn_refresh = QPushButton("↻")
        self.btn_refresh.setToolTip("Refrescar lista")
        self.btn_refresh.setFont(QFont("Arial", 10))
        self.btn_refresh.clicked.connect(self.refresh)
        self.btn_refresh.setFixedWidth(40)
        
        nav_layout.addWidget(self.btn_up)
        nav_layout.addWidget(self.lbl_path)
        nav_layout.addStretch()
        nav_layout.addWidget(self.btn_refresh)
        layout.addLayout(nav_layout)
        
        # Lista de carpetas
        self.list_widget = QListWidget()
        self.list_widget.setFont(QFont("Arial", 11))
        self.list_widget.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.list_widget)
        
        # Botón para seleccionar carpeta actual
        self.btn_select = QPushButton("Seleccionar esta carpeta")
        self.btn_select.setIcon(QIcon(":/icons/folder_select.png"))
        self.btn_select.setStyleSheet("""
            QPushButton {
                background-color: #2980B9; color: white; padding: 8px;
                border-radius: 6px; font-weight: bold;
            }
            QPushButton:hover { background-color: #3498DB; }
        """)
        self.btn_select.clicked.connect(self.select_current_folder)
        layout.addWidget(self.btn_select)
        
        self.setLayout(layout)
    
    def refresh(self):
        """Actualiza la vista del directorio actual"""
        try:
            # Normalizar ruta para el servidor
            normalized_path = self.current_path.replace('\\', '/') if self.current_path else ""
            
            data = self.client.list_directory(normalized_path)
            self.list_widget.clear()
            
            # Mostrar carpeta padre si no estamos en raíz
            if normalized_path:
                item = QListWidgetItem(".. (directorio padre)")
                item.setData(Qt.ItemDataRole.UserRole, os.path.dirname(normalized_path))
                item.setIcon(QIcon(":/icons/folder_up.png"))
                self.list_widget.addItem(item)
            
            # Mostrar carpetas
            for folder in data.get("folders", []):
                item = QListWidgetItem(f"📁 {folder}")
                item.setData(Qt.ItemDataRole.UserRole, os.path.join(normalized_path, folder))
                item.setIcon(QIcon(":/icons/folder.png"))
                self.list_widget.addItem(item)
            
            # Actualizar barra de ruta
            display_path = normalized_path if normalized_path else "/ (raíz)"
            self.lbl_path.setText(display_path)
            
            # Habilitar/deshabilitar botón de subir
            self.btn_up.setEnabled(bool(normalized_path))
            
        except Exception as e:
            # Manejar error mostrando mensaje en la lista
            error_item = QListWidgetItem(f"⚠️ Error al cargar directorio: {str(e)}")
            error_item.setForeground(QBrush(QColor(255, 0, 0)))
            self.list_widget.addItem(error_item)
    
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
    
    def select_current_folder(self):
        """Selecciona la carpeta actual para experimentos"""
        self.folder_selected.emit(self.current_path)
    
    def get_current_path(self):
        """Devuelve la ruta relativa actual"""
        return self.current_path