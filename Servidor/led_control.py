import RPi.GPIO as GPIO
import time

class LedController:
    def __init__(self, cam_pin_map):
        """
        cam_pin_map: dict {camera_id: gpio_pin}
        """
        self.cam_pin_map = cam_pin_map
        GPIO.setmode(GPIO.BCM)
        for pin in cam_pin_map.values():
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

    def on(self, cam_id):
        pin = self.cam_pin_map.get(cam_id)
        if pin is not None:
            GPIO.output(pin, GPIO.HIGH)

    def off(self, cam_id):
        pin = self.cam_pin_map.get(cam_id)
        if pin is not None:
            GPIO.output(pin, GPIO.LOW)

    def all_on(self):
        for cam_id in self.cam_pin_map:
            self.on(cam_id)

    def all_off(self):
        for cam_id in self.cam_pin_map:
            self.off(cam_id)

    def set_intensity(self, cam_id, duty_cycle):
        """
        Opcional: si usas PWM para controlar intensidad del LED.
        duty_cycle: 0-100
        """
        pin = self.cam_pin_map.get(cam_id)
        if pin is None:
            return

        if not hasattr(self, '_pwm'):
            self._pwm = {}

        if cam_id not in self._pwm:
            pwm = GPIO.PWM(pin, 1000)  # 1 kHz
            pwm.start(duty_cycle)
            self._pwm[cam_id] = pwm
        else:
            self._pwm[cam_id].ChangeDutyCycle(duty_cycle)

    def cleanup(self):
        if hasattr(self, '_pwm'):
            for pwm in self._pwm.values():
                pwm.stop()
        GPIO.cleanup()
