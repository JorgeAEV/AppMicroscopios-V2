# dht_sensor.py
import Adafruit_DHT

SENSOR = Adafruit_DHT.DHT11
PIN = 4  # GPIO conectado al DHT11

def read_dht():
    humidity, temperature = Adafruit_DHT.read_retry(SENSOR, PIN)
    return {
        'temperature': temperature if temperature is not None else -1,
        'humidity': humidity if humidity is not None else -1
    }
