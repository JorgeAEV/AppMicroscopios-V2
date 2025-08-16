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

        self._thread = None
        self._stop_event = threading.Event()
        self.running = False

    def start(self, save_path, duration_sec, interval_sec):
        if self.running:
            raise RuntimeError("Experimento ya en ejecución")

        self.save_path = save_path
        self.duration = duration_sec
        self.interval = interval_sec

        # La carpeta principal ya fue creada por el servidor
        # Solo necesitamos crear las subcarpetas por cámara
        for cam_id in self.camera_manager.cameras:
            cam_folder = os.path.join(self.save_path, f"Microscopio{cam_id}")
            os.makedirs(cam_folder, exist_ok=True)

        self._stop_event.clear()
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        start_time = time.time()
        next_capture = start_time
        while not self._stop_event.is_set() and (time.time() - start_time < self.duration):
            now = time.time()
            if now >= next_capture:
                self._capture_all()
                next_capture += self.interval
            else:
                time.sleep(0.5)
        self.running = False
        # Asegurar apagar leds al terminar
        self.led_controller.all_off()

    def _capture_all(self):
        # Enciende leds para cada cámara
        self.led_controller.all_on()
        time.sleep(0.5)  # Tiempo para estabilizar iluminación

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Obtener lectura sensor
        dht_data = self.dht_sensor.get_readings()

        # Guardar lectura en archivo resumen (append)
        resumen_path = os.path.join(self.save_path, "resumen_dht.txt")
        with open(resumen_path, 'a') as f:
            f.write(f"{timestamp} - Temp: {dht_data['temperature']}C, Humidity: {dht_data['humidity']}%\n")

        # Tomar fotos y guardar
        for cam_id in self.camera_manager.cameras:
            cam_folder = os.path.join(self.save_path, f"Microscopio{cam_id}")
            photo_path = os.path.join(cam_folder, f"{timestamp}.jpg")
            try:
                self.camera_manager.take_photo(cam_id, photo_path)
            except Exception as e:
                print(f"Error tomando foto cámara {cam_id}: {e}")

        # Apagar leds después de tomar fotos
        self.led_controller.all_off()

    def stop(self):
        if not self.running:
            return
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        self.running = False
        self.led_controller.all_off()