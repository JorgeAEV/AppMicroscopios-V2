import cv2
import threading
import time
from datetime import datetime
import os

class CameraManager:
    def __init__(self, max_cams=5):
        self.max_cams = max_cams
        self.cameras = self.detect_cameras()                  # [0,1,2,...]
        self.locks = {cam: threading.Lock() for cam in self.cameras}
        self.captures = {cam: cv2.VideoCapture(cam) for cam in self.cameras}
        self.running = True

    # ---------- Descubrimiento / utilidades ----------
    def detect_cameras(self):
        cams = []
        for i in range(self.max_cams):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                cams.append(i)
                cap.release()
        return cams

    def get_cameras(self):
        """Devuelve la lista actual de IDs de cámaras disponibles."""
        return list(self.cameras)

    def refresh_cameras(self):
        """
        Re-detecta cámaras y abre/cierra capturas según haga falta.
        Mantiene locks para cámaras que persisten; crea para nuevas; elimina para las que ya no están.
        """
        found = self.detect_cameras()
        new_set, old_set = set(found), set(self.cameras)

        # Cerrar las que ya no existen
        for cam in (old_set - new_set):
            try:
                cap = self.captures.pop(cam, None)
                if cap is not None:
                    cap.release()
            except Exception:
                pass
            self.locks.pop(cam, None)

        # Crear las nuevas
        for cam in (new_set - old_set):
            self.locks[cam] = threading.Lock()
            self.captures[cam] = cv2.VideoCapture(cam)

        self.cameras = sorted(found)

    # ---------- Internos ----------
    def _ensure_open_locked(self, cam_id):
        """
        Asegura (con lock del cam_id ya tomado) que la captura esté abierta.
        Si no lo está, intenta reabrir una vez.
        """
        cap = self.captures.get(cam_id)
        if cap is None or not cap.isOpened():
            # Re-crear el VideoCapture
            cap = cv2.VideoCapture(cam_id)
            self.captures[cam_id] = cap
        return cap if cap.isOpened() else None

    # ---------- Streaming ----------
    def generate_frames(self, cam_id):
        if cam_id not in self.cameras:
            return
        cap = self.captures[cam_id]
        while self.running:
            with self.locks[cam_id]:
                # Asegura que la cámara esté abierta
                cap = self._ensure_open_locked(cam_id)
                if cap is None:
                    time.sleep(0.2)
                    continue
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

    # ---------- Captura puntual por cámara (para experimentos por subconjunto) ----------
    def grab_frame(self, cam_id):
        """
        Devuelve un frame (numpy array BGR) de la cámara indicada o None si falla.
        Reabre la cámara si se cerró. Thread-safe por cámara.
        """
        if cam_id not in self.cameras:
            return None
        with self.locks[cam_id]:
            cap = self._ensure_open_locked(cam_id)
            if cap is None:
                return None
            ok, frame = cap.read()
            if not ok:
                # Reintenta breve 1 vez por si fue un glitch
                time.sleep(0.05)
                ok, frame = cap.read()
                if not ok:
                    return None
            return frame

    def save_snapshot(self, cam_id, out_path):
        """
        Guarda una imagen JPEG de la cámara cam_id en out_path.
        Devuelve True si se guardó, False si no.
        """
        frame = self.grab_frame(cam_id)
        if frame is None:
            return False
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        return cv2.imwrite(out_path, frame)

    # ---------- Compatibilidad con tu API actual ----------
    def take_photo(self, cam_id, save_path):
        """
        Toma una foto de la cámara indicada y la guarda en save_path (.jpg).
        Mantiene comportamiento original (lanza excepción si falla),
        pero internamente usa save_snapshot para robustez.
        """
        if cam_id not in self.cameras:
            raise ValueError(f"Cámara {cam_id} no detectada")
        ok = self.save_snapshot(cam_id, save_path)
        if not ok:
            raise RuntimeError("No se pudo capturar imagen")

    # ---------- Liberación ----------
    def release(self):
        self.running = False
        for cap in list(self.captures.values()):
            try:
                cap.release()
            except Exception:
                pass
