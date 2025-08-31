import threading
import time
import os
from datetime import datetime


class Experiment:
    def __init__(self, camera_manager, led_controller, dht_sensor):
        self.camera_manager = camera_manager
        self.led_controller = led_controller
        self.dht_sensor = dht_sensor

        self.save_path = None
        self.duration = 0  # segundos
        self.interval = 0  # segundos

        # NUEVO: subconjunto activo de cámaras (lista de enteros)
        self.camera_ids = None

        self._thread = None
        self._stop_event = threading.Event()
        self.running = False

    # ================== API ==================
    def start(self, save_path, duration_sec, interval_sec, camera_ids=None):
        """
        Inicia el experimento. Si camera_ids es None o vacío, usa todas las detectadas.
        """
        if self.running:
            raise RuntimeError("Experimento ya en ejecución")

        self.save_path = save_path
        self.duration = int(duration_sec)
        self.interval = int(interval_sec)

        # Sanitiza subconjunto de cámaras
        if camera_ids:
            # Filtra a sólo cámaras válidas detectadas por CameraManager
            detected = set(self.camera_manager.cameras)
            self.camera_ids = sorted({int(c) for c in camera_ids if int(c) in detected})
            if not self.camera_ids:
                # Si la lista viene inválida, cae en todas
                self.camera_ids = sorted(list(detected))
        else:
            self.camera_ids = sorted(list(self.camera_manager.cameras))

        # Crear subcarpetas sólo para las cámaras seleccionadas
        for cam_id in self.camera_ids:
            cam_folder = os.path.join(self.save_path, f"Microscopio{cam_id}")
            os.makedirs(cam_folder, exist_ok=True)

        # Crear/abrir archivo de resumen al inicio (DHT)
        resumen_path = os.path.join(self.save_path, "resumen_dht.txt")
        os.makedirs(self.save_path, exist_ok=True)
        with open(resumen_path, 'w') as f:
            f.write("=== Resumen de lecturas DHT11 ===\n")

        self._stop_event.clear()
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if not self.running:
            return
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        self.running = False
        self._led_off_selected()

    # ================== Internos ==================
    def _run(self):
        start_time = time.time()
        next_capture = start_time

        try:
            while not self._stop_event.is_set() and (time.time() - start_time < self.duration):
                now = time.time()
                if now >= next_capture:
                    self._capture_tick()
                    # Programa el siguiente tick sumando interval (evita drift acumulado grande)
                    next_capture += self.interval
                else:
                    time.sleep(0.1)
        finally:
            self.running = False
            self._led_off_selected()

    def _capture_tick(self):
        # Encender LEDs sólo de cámaras seleccionadas (si hay API por-cámara); si no, fallback a all_on()
        self._led_on_selected()
        time.sleep(0.5)  # Tiempo para estabilizar iluminación

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # === Lectura DHT11 ===
        resumen_path = os.path.join(self.save_path, "resumen_dht.txt")
        try:
            dht_data = self.dht_sensor.read() if self.dht_sensor else None
        except Exception as e:
            dht_data = None
            # Se registra como fallida abajo

        with open(resumen_path, 'a') as f:
            if dht_data and dht_data.get("temperature") is not None and dht_data.get("humidity") is not None:
                f.write(f"{timestamp} - Temp: {dht_data['temperature']:.1f}C, "
                        f"Humidity: {dht_data['humidity']:.1f}%\n")
            else:
                f.write(f"{timestamp} - Lectura DHT11 fallida\n")

        # === Captura de fotos sólo de cámaras seleccionadas ===
        for cam_id in self.camera_ids:
            cam_folder = os.path.join(self.save_path, f"Microscopio{cam_id}")
            photo_path = os.path.join(cam_folder, f"{timestamp}.jpg")
            try:
                # Puedes usar take_photo (compat) o save_snapshot (más robusto) si lo añadiste al CameraManager
                if hasattr(self.camera_manager, "save_snapshot"):
                    ok = self.camera_manager.save_snapshot(cam_id, photo_path)
                    if not ok:
                        raise RuntimeError("save_snapshot devolvió False")
                else:
                    self.camera_manager.take_photo(cam_id, photo_path)
            except Exception as e:
                print(f"[Experiment] Error tomando foto cámara {cam_id}: {e}")

        # Apagar LEDs seleccionados / todos según disponibilidad
        self._led_off_selected()

    # ================== LEDs helpers ==================
    def _led_on_selected(self):
        """
        Intenta encender sólo los LEDs de las cámaras seleccionadas si el LedController
        lo soporta (on_for_camera / set_for_camera / blink_for_camera); si no, usa all_on().
        """
        if not self.led_controller:
            return
        try:
            # Preferencia: set por cámara si existe
            if hasattr(self.led_controller, "on_for_camera"):
                for cam_id in self.camera_ids:
                    self.led_controller.on_for_camera(cam_id)
            elif hasattr(self.led_controller, "set_for_camera"):
                for cam_id in self.camera_ids:
                    self.led_controller.set_for_camera(cam_id, True)
            else:
                # Fallback
                self.led_controller.all_on()
        except Exception:
            # No romper el experimento por el LED
            pass

    def _led_off_selected(self):
        """
        Intenta apagar sólo los LEDs de las cámaras seleccionadas si el LedController
        lo soporta; si no, usa all_off().
        """
        if not self.led_controller:
            return
        try:
            if hasattr(self.led_controller, "off_for_camera"):
                for cam_id in self.camera_ids or []:
                    self.led_controller.off_for_camera(cam_id)
            elif hasattr(self.led_controller, "set_for_camera"):
                for cam_id in self.camera_ids or []:
                    self.led_controller.set_for_camera(cam_id, False)
            else:
                self.led_controller.all_off()
        except Exception:
            pass
