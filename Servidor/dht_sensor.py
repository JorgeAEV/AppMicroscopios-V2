import adafruit_dht
import threading
import time

class DHTSensor:
    def __init__(self, pin, read_interval=5):
        """
        pin: objeto board.Dxx (ejemplo: board.D4)
        read_interval: intervalo en segundos entre lecturas
        """
        self.sensor = adafruit_dht.DHT11(pin)
        self.read_interval = read_interval
        self.temperature = None
        self.humidity = None
        self.running = False
        self._thread = None
        self._lock = threading.Lock()

    def start(self):
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _read_loop(self):
        while self.running:
            try:
                # Intentar leer valores
                temperature = self.sensor.temperature
                humidity = self.sensor.humidity

                with self._lock:
                    self.temperature = temperature
                    self.humidity = humidity

            except Exception as e:
                # El DHT11 suele dar errores ocasionales, manejarlos aquí
                print(f"Error leyendo DHT11: {e}")
                with self._lock:
                    self.temperature = None
                    self.humidity = None

            time.sleep(self.read_interval)

    def get_readings(self):
        with self._lock:
            return {
                'temperature': self.temperature,
                'humidity': self.humidity
            }

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join()
