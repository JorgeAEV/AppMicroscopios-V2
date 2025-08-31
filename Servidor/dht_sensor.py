import adafruit_dht
import board
import threading
import time

class DHTSensor:
    def __init__(self, pin=4, read_interval=5):
        """
        pin: número del GPIO (ejemplo 4 -> GPIO4)
        read_interval: intervalo en segundos entre lecturas
        """
        # Convertimos el pin a objeto board (ejemplo: 4 -> board.D4)
        self.pin = getattr(board, f"D{pin}")
        self.sensor = adafruit_dht.DHT11(self.pin)

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
                # Lectura de temperatura y humedad
                temperature = self.sensor.temperature
                humidity = self.sensor.humidity

                with self._lock:
                    self.temperature = temperature
                    self.humidity = humidity

            except Exception as e:
                # Si ocurre error (muy común con DHT11), guardamos None
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
