import Adafruit_DHT
import threading
import time

class DHTSensor:
    def __init__(self, pin, sensor_type=Adafruit_DHT.DHT11, read_interval=5):
        self.pin = pin
        self.sensor_type = sensor_type
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
            humidity, temperature = Adafruit_DHT.read_retry(self.sensor_type, self.pin)
            with self._lock:
                self.temperature = temperature
                self.humidity = humidity
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
