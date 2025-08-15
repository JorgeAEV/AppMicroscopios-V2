import cv2
import numpy as np
import matplotlib.pyplot as plt
import tempfile
import requests

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


def show_rgb_histogram(image_path):
    """Muestra el histograma RGB en una ventana nueva."""
    img = cv2.imread(image_path)
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


def show_brightness_histogram(image_path):
    """Muestra el histograma de brillo (en escala de grises) en una ventana nueva."""
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    plt.figure("Histograma de Brillo")
    plt.plot(hist, color='black')
    plt.xlim([0, 256])
    plt.title("Histograma de Brillo")
    plt.xlabel("Nivel de brillo")
    plt.ylabel("Frecuencia")
    plt.show()
