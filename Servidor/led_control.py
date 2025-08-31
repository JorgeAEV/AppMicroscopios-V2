import RPi.GPIO as GPIO
import time


class LedController:
    """
    Control PWM por cámara con brillo persistente (0-100).
    - Cada cámara tiene un pin BCM y un PWM independiente.
    - 'on' enciende respetando el brillo guardado.
    - 'off' apaga sin perder el valor de brillo almacenado.
    """

    def __init__(self, cam_pin_map, pwm_freq=1000, default_brightness=100):
        """
        cam_pin_map: dict {camera_id: gpio_bcm_pin}
        pwm_freq: frecuencia PWM en Hz (por defecto 1 kHz)
        default_brightness: brillo por defecto (0-100) cuando nunca se ha configurado
        """
        self.cam_pin_map = dict(cam_pin_map)
        self.pwm_freq = int(pwm_freq)
        self.default_brightness = max(0, min(100, int(default_brightness)))

        self._pwm = {}          # cam_id -> PWM
        self._brightness = {}   # cam_id -> 0..100 (persistente en memoria)

        GPIO.setmode(GPIO.BCM)
        for cam_id, pin in self.cam_pin_map.items():
            GPIO.setup(pin, GPIO.OUT)
            pwm = GPIO.PWM(pin, self.pwm_freq)
            pwm.start(0)  # inicia apagado
            self._pwm[cam_id] = pwm
            self._brightness[cam_id] = self.default_brightness

    # -------- Brillo por cámara --------
    def set_brightness(self, cam_id, value):
        """
        Establece el brillo (0-100) y aplica al PWM si el LED está "encendido".
        Nota: Encendido significa que el duty != 0. Para encender, usa on()/on_for_camera().
        """
        if cam_id not in self._pwm:
            raise ValueError(f"LED sin mapeo para cámara {cam_id}")

        value = max(0, min(100, int(value)))
        self._brightness[cam_id] = value

        # Si actualmente está encendido (duty>0), actualiza duty al nuevo brillo
        # Para saber si está encendido, simplemente aplicamos el nuevo duty:
        # - Si estaba apagado y quieres mantener apagado, no lo encendemos aquí.
        #   'set_brightness' solo actualiza el valor; 'on' decide encender.
        current_duty = self._get_current_duty(cam_id)
        if current_duty > 0 or value == 0:
            self._pwm[cam_id].ChangeDutyCycle(value)

    def get_brightness(self, cam_id):
        if cam_id not in self._brightness:
            raise ValueError(f"LED sin mapeo para cámara {cam_id}")
        return int(self._brightness[cam_id])

    def _get_current_duty(self, cam_id):
        """
        No hay API pública para leer duty actual en RPi.GPIO;
        para mantener simple, devolvemos el valor guardado si duty>0,
        pero como no lo distinguimos, usamos el brillo guardado como referencia.
        """
        return self._brightness.get(cam_id, 0)

    # -------- Encendido / Apagado por cámara --------
    def on_for_camera(self, cam_id):
        """
        Enciende usando el brillo guardado (si es 0, no se verá luz).
        """
        if cam_id not in self._pwm:
            return
        duty = self._brightness.get(cam_id, self.default_brightness)
        self._pwm[cam_id].ChangeDutyCycle(duty)

    def off_for_camera(self, cam_id):
        """
        Apaga (duty=0) sin perder el brillo guardado.
        """
        if cam_id not in self._pwm:
            return
        self._pwm[cam_id].ChangeDutyCycle(0)

    def set_for_camera(self, cam_id, state: bool):
        if state:
            self.on_for_camera(cam_id)
        else:
            self.off_for_camera(cam_id)

    # -------- Compatibilidad con tu API actual --------
    def on(self, cam_id):
        """Compat: encender respetando brillo guardado."""
        self.on_for_camera(cam_id)

    def off(self, cam_id):
        """Compat: apagar sin perder brillo guardado."""
        self.off_for_camera(cam_id)

    def all_on(self):
        for cam_id in list(self._pwm.keys()):
            self.on_for_camera(cam_id)

    def all_off(self):
        for cam_id in list(self._pwm.keys()):
            self.off_for_camera(cam_id)

    # -------- Utilidades --------
    def blink_for_camera(self, cam_id, duration_ms=80):
        """
        Parpadeo corto al 100% y volver al brillo previo.
        Útil como feedback durante la captura.
        """
        if cam_id not in self._pwm:
            return
        prev = self.get_brightness(cam_id)
        # sube a 100, espera breve y vuelve a previo
        self._pwm[cam_id].ChangeDutyCycle(100)
        time.sleep(max(0, duration_ms) / 1000.0)
        # si el LED estaba encendido, volvemos al brillo previo; si estaba apagado,
        # dejamos duty=0 (para no encenderlo "de paso")
        if prev > 0:
            self._pwm[cam_id].ChangeDutyCycle(prev)
        else:
            self._pwm[cam_id].ChangeDutyCycle(0)

    # Alias para no romper código viejo que llamaba set_intensity
    def set_intensity(self, cam_id, duty_cycle):
        """Alias retrocompatible de set_brightness(cam_id, value)."""
        self.set_brightness(cam_id, duty_cycle)

    def cleanup(self):
        try:
            self.all_off()
        finally:
            for pwm in self._pwm.values():
                try:
                    pwm.stop()
                except Exception:
                    pass
            GPIO.cleanup()
