# utils.py
import cv2
import matplotlib.pyplot as plt

def generate_rgb_histogram(image_path):
    image = cv2.imread(image_path)
    if image is None:
        print("No se pudo cargar la imagen.")
        return
    colors = ('b', 'g', 'r')
    for i, col in enumerate(colors):
        hist = cv2.calcHist([image], [i], None, [256], [0, 256])
        plt.plot(hist, color=col)
    plt.title("Histograma RGB")
    plt.xlabel("Intensidad")
    plt.ylabel("Cantidad de píxeles")
    plt.show()
