# led_control.py
import RPi.GPIO as GPIO
import time

# Configurar modo
GPIO.setmode(GPIO.BCM)

# Diccionario de LEDs por cámara (ajustar pines según conexiones reales)
LED_PINS = {
    0: 17,
    1: 27,
    2: 22,
    3: 23
}

# Inicializar
for pin in LED_PINS.values():
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

def turn_on_led(camera_id):
    pin = LED_PINS.get(camera_id)
    if pin is not None:
        GPIO.output(pin, GPIO.HIGH)

def turn_off_led(camera_id):
    pin = LED_PINS.get(camera_id)
    if pin is not None:
        GPIO.output(pin, GPIO.LOW)

def cleanup():
    GPIO.cleanup()
