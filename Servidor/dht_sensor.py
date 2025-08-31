# dht_sensor.py
import time
import board
import adafruit_dht

class DHTSensor:
    def __init__(self, pin=4, retries=5, delay=1.0):
        """
        Clase para interactuar con el sensor DHT11 de manera sencilla.
        
        :param pin: Número de pin BCM donde está conectado el DHT11 (ej. 4)
        :param retries: Número de intentos por lectura
        :param delay: Tiempo en segundos entre reintentos
        """
        # Convertir pin BCM al objeto correspondiente de board
        self.pin = getattr(board, f"D{pin}")
        self.sensor = adafruit_dht.DHT11(self.pin)
        self.retries = retries
        self.delay = delay

    def read(self):
        """
        Intenta obtener una lectura válida del sensor.
        Devuelve un diccionario con:
            {"temperature": float|None, "humidity": float|None}
        Si tras varios intentos no logra lectura válida, devuelve ambos None.
        """
        for attempt in range(self.retries):
            try:
                temperature = self.sensor.temperature
                humidity = self.sensor.humidity
                if temperature is not None and humidity is not None:
                    return {"temperature": temperature, "humidity": humidity}
            except Exception as e:
                # Errores comunes: buffer incompleto, checksum inválido, etc.
                print(f"Error leyendo DHT11 (intento {attempt+1}/{self.retries}): {e}")
            time.sleep(self.delay)

        # Si nunca logró leer, devolvemos None
        return {"temperature": None, "humidity": None}

    def cleanup(self):
        """Libera el recurso asociado al sensor."""
        try:
            self.sensor.exit()
        except Exception:
            pass
