# 📷 Sistema de Monitoreo con Raspberry Pi 3B y Cámaras USB

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![PyQt](https://img.shields.io/badge/PyQt-6.0-green)
![Flask](https://img.shields.io/badge/Flask-2.0-lightgrey)

Sistema cliente-servidor para captura de imágenes sincronizada con monitoreo ambiental, diseñado para experimentos científicos con múltiples cámaras USB.

## 🔍 Descripción

Este proyecto permite:
- Controlar múltiples cámaras USB conectadas a una Raspberry Pi 3B
- Sincronizar la captura de imágenes con iluminación mediante LEDs
- Monitorear condiciones ambientales (temperatura/humedad) con sensor DHT11
- Configurar experimentos con temporización precisa
- Visualizar imágenes en tiempo real desde una interfaz gráfica

## 🧩 Componentes Hardware

| Componente      | Descripción                           |
|-----------------|---------------------------------------|
| Raspberry Pi 3B | Unidad central de procesamiento       |
| Cámaras USB     | Hasta 4 cámaras simultáneas           |
| LEDs            | Iluminación controlada (1 por cámara) |
| Sensor DHT11    | Medición de temperatura y humedad     |
| Resistores      | 220Ω para protección de LEDs          |

## 🖥️ Interfaz Cliente (PyQt6)

### Pestañas Principales

1. **Bienvenida/Estado**
   - Detección automática de cámaras
   - Panel de monitoreo del sistema:
     - Temperatura de la CPU
     - Uso de RAM y CPU
     - Almacenamiento disponible

2. **Visualización de Cámaras**
   - Navegación por pestañas entre cámaras
   - Transmisión en vivo
   - Acceso rápido a calibración

3. **Modo Calibración**
   - Control de intensidad LED (0-100%)
   - Herramientas de análisis:
     - Histograma RGB
     - Brillo promedio
   - Previsualización en tiempo real

4. **Control de Experimentos**
   - Configuración de parámetros:
     - Duración total
     - Intervalo entre capturas
     - Ruta de guardado
   - Monitoreo en tiempo real
   - Capacidad de cancelación

## 🖥️ Servidor (Flask)

### Funcionalidades

- API REST para comunicación con cliente
- Control preciso de hardware:
  - Encendido/apagado sincronizado de LEDs
  - Captura de imágenes programada
  - Lectura de sensor ambiental
- Optimización de recursos para operación continua
- Registro de eventos y errores

## 🛠️ Instalación

### Requisitos

- Python 3.8+
- Raspberry Pi OS (32-bit)
- Librerías (instalar con `pip install -r requirements.txt`):

```bash
# requirements.txt
PyQt6==6.4.0
Flask==2.2.2
opencv-python-headless==4.6.0.66
numpy==1.23.5
RPi.GPIO==0.7.1
Adafruit-DHT==1.4.0
psutil==5.9.4