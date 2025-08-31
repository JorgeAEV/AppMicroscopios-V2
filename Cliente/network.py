import requests
from requests.exceptions import RequestException
from config import BASE_URL


class NetworkClient:
    def __init__(self):
        self.base_url = BASE_URL.rstrip("/")

    # ---------- Cámaras / Streaming ----------
    def get_cameras(self):
        try:
            r = requests.get(f"{self.base_url}/cameras", timeout=5)
            r.raise_for_status()
            # El servidor devuelve lista de enteros
            return r.json()
        except RequestException:
            return []

    def get_video_feed_url(self, cam_id):
        return f"{self.base_url}/video_feed/{cam_id}"

    # ---------- LEDs: ON/OFF por cámara ----------
    def led_control(self, cam_id, action):
        """
        action: 'on' | 'off'
        """
        try:
            r = requests.post(f"{self.base_url}/led/{cam_id}/{action}", timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException:
            return {"status": "error", "message": "Error de conexión"}

    # ---------- LEDs: brillo por cámara ----------
    def set_led_brightness(self, cam_id, value):
        """
        value: 0..100 (duty cycle)
        No enciende automáticamente; sólo actualiza el valor.
        """
        try:
            payload = {"value": int(value)}
            r = requests.post(f"{self.base_url}/led/{cam_id}/brightness", json=payload, timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException as e:
            return {"status": "error", "message": str(e)}

    def get_led_brightness(self, cam_id):
        try:
            r = requests.get(f"{self.base_url}/led/{cam_id}/brightness", timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException as e:
            return {"status": "error", "message": str(e)}

    def get_led_brightness_map(self):
        """
        Devuelve {'status':'ok','values': {cam_id: brillo, ...}}
        """
        try:
            r = requests.get(f"{self.base_url}/led/brightness_map", timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException as e:
            return {"status": "error", "message": str(e)}

    # ---------- LEDs: global ----------
    def led_all(self, action):
        """
        action: 'on' | 'off'
        """
        try:
            r = requests.post(f"{self.base_url}/led/all/{action}", timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException as e:
            return {"status": "error", "message": str(e)}

    # ---------- Sensor ----------
    def get_sensor_data(self):
        try:
            r = requests.get(f"{self.base_url}/sensor", timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException:
            return {}

    # ---------- Experimento ----------
    def start_experiment(self, save_path, duration, interval, camera_ids=None):
        """
        Inicia un experimento. Si camera_ids es None o [], el servidor usará todas las cámaras.
        """
        try:
            payload = {
                "save_path": save_path,
                "duration": int(duration),
                "interval": int(interval),
            }
            if camera_ids:
                payload["camera_ids"] = list(map(int, camera_ids))
            r = requests.post(f"{self.base_url}/experiment/start", json=payload, timeout=8)
            r.raise_for_status()
            return r.json()
        except RequestException as e:
            return {"status": "error", "message": str(e)}

    def stop_experiment(self):
        try:
            r = requests.post(f"{self.base_url}/experiment/stop", timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException as e:
            return {"status": "error", "message": str(e)}

    # ---------- Servidor ----------
    def shutdown_server(self):
        try:
            r = requests.post(f"{self.base_url}/shutdown", timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException as e:
            return {"status": "error", "message": str(e)}

    def get_status(self):
        """
        Devuelve el estado del sistema y del experimento.
        Estructura esperada:
        {
          "system": {...},
          "experiment": {
              "running": bool,
              "save_path": str|None,
              "duration": int,
              "interval": int,
              "camera_ids": [int,...] | None,
              "led_brightness": {cam_id: brillo|None}
          }
        }
        """
        try:
            r = requests.get(f"{self.base_url}/status", timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException:
            return {}

    def get_experiment_status(self):
        """
        Atajo para extraer sólo el bloque 'experiment' del /status.
        """
        data = self.get_status() or {}
        return data.get("experiment", {}) if isinstance(data, dict) else {}

    # ---------- Archivos / Carpetas ----------
    def list_directory(self, sub_path=""):
        """
        Obtiene la lista de carpetas y archivos dentro de un subdirectorio del directorio base.
        Lanza Exception con mensaje de alto nivel si algo falla.
        """
        try:
            params = {"path": sub_path} if sub_path else {}
            r = requests.get(f"{self.base_url}/list_dir", params=params, timeout=5)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "success":
                return data
            else:
                raise Exception(data.get("message", "Error al listar directorio"))
        except (RequestException, ValueError) as e:
            raise Exception(f"No se pudo listar directorio: {e}")

    def create_folder(self, folder_path):
        """
        Crea una carpeta (o estructura de carpetas) en el servidor.
        """
        try:
            payload = {"folder_path": folder_path}
            r = requests.post(f"{self.base_url}/create_folder", json=payload, timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}
