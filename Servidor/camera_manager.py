import cv2
import threading
import time
from datetime import datetime
import os

class CameraManager:
    def __init__(self, max_cams=5):
        self.max_cams = max_cams
        self.cameras = self.detect_cameras()
        self.locks = {cam: threading.Lock() for cam in self.cameras}
        self.captures = {cam: cv2.VideoCapture(cam) for cam in self.cameras}
        self.running = True

    def detect_cameras(self):
        cams = []
        for i in range(self.max_cams):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cams.append(i)
                cap.release()
        return cams

    def generate_frames(self, cam_id):
        if cam_id not in self.cameras:
            return
        cap = self.captures[cam_id]
        while self.running:
            with self.locks[cam_id]:
                ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue
            ret2, buffer = cv2.imencode('.jpg', frame)
            if not ret2:
                continue
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.03)  # ~30 FPS cap

    def take_photo(self, cam_id, save_path):
        """
        Toma una foto de la cámara indicada y la guarda en save_path.
        save_path debe incluir nombre y extensión (.jpg)
        """
        if cam_id not in self.cameras:
            raise ValueError(f"Cámara {cam_id} no detectada")
        with self.locks[cam_id]:
            cap = self.captures[cam_id]
            ret, frame = cap.read()
            if not ret:
                raise RuntimeError("No se pudo capturar imagen")
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            cv2.imwrite(save_path, frame)

    def release(self):
        self.running = False
        for cap in self.captures.values():
            cap.release()
