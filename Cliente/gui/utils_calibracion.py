import cv2
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import requests
from PyQt6.QtGui import QImage

def fetch_camera_image(camera_index, server_url):
    """Obtiene una imagen actual desde la cámara seleccionada en el servidor."""
    try:
        response = requests.get(f"{server_url}/capture_image/{camera_index}", stream=True)
        if response.status_code == 200:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
            with open(temp_file.name, "wb") as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
            return temp_file.name
        else:
            print(f"Error al obtener imagen: {response.status_code}")
    except Exception as e:
        print(f"Error en fetch_camera_image: {e}")
    return None


def show_rgb_histogram(image_source):
    if isinstance(image_source, str):
        img = cv2.imread(image_source)
    else:
        img = qimage_to_cv(image_source)
    
    if img is None:
        print("Error: No se pudo obtener la imagen")
        return

    color = ('b', 'g', 'r')
    plt.figure("Histograma RGB")
    for i, col in enumerate(color):
        histr = cv2.calcHist([img], [i], None, [256], [0, 256])
        plt.plot(histr, color=col)
        plt.xlim([0, 256])
    plt.title("Histograma RGB")
    plt.xlabel("Intensidad de color")
    plt.ylabel("Frecuencia")
    plt.show()

def show_brightness_histogram(image_source):
    if isinstance(image_source, str):
        img = cv2.imread(image_source, cv2.IMREAD_GRAYSCALE)
    else:
        img = qimage_to_cv(image_source, grayscale=True)
    
    if img is None:
        print("Error: No se pudo obtener la imagen")
        return

    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    plt.figure("Histograma de Brillo")
    plt.plot(hist, color='black')
    plt.xlim([0, 256])
    plt.title("Histograma de Brillo")
    plt.xlabel("Nivel de brillo")
    plt.ylabel("Frecuencia")
    plt.show()

def qimage_to_cv(qimage, grayscale=False):
    """Convierte QImage a formato OpenCV usando sizeInBytes()"""
    # Convertir a formato RGB888
    if qimage.format() != QImage.Format.Format_RGB888:
        qimage = qimage.convertToFormat(QImage.Format.Format_RGB888)
    
    width, height = qimage.width(), qimage.height()
    ptr = qimage.bits()
    ptr.setsize(qimage.sizeInBytes())  # Usar sizeInBytes() en PyQt6
    
    # Crear array numpy y remodelar
    arr = np.frombuffer(ptr, dtype=np.uint8).reshape((height, width, 3))
    
    # Convertir RGB a BGR
    bgr_image = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    
    return cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY) if grayscale else bgr_image