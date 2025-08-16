import requests
from requests.exceptions import RequestException
from config import BASE_URL

class NetworkClient:
    def __init__(self):
        self.base_url = BASE_URL

    def get_cameras(self):
        try:
            r = requests.get(f"{self.base_url}/cameras", timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException:
            return []

    def get_video_feed_url(self, cam_id):
        return f"{self.base_url}/video_feed/{cam_id}"

    def led_control(self, cam_id, action):
        try:
            r = requests.post(f"{self.base_url}/led/{cam_id}/{action}", timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException:
            return {'status': 'error', 'message': 'Error de conexión'}

    def get_sensor_data(self):
        try:
            r = requests.get(f"{self.base_url}/sensor", timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException:
            return {}

    def start_experiment(self, save_path, duration, interval):
        try:
            payload = {
                'save_path': save_path,
                'duration': duration,
                'interval': interval
            }
            r = requests.post(f"{self.base_url}/experiment/start", json=payload, timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException as e:
            return {'status': 'error', 'message': str(e)}

    def stop_experiment(self):
        try:
            r = requests.post(f"{self.base_url}/experiment/stop", timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException as e:
            return {'status': 'error', 'message': str(e)}
    
    def shutdown_server(self):
        try:
            r = requests.post(f"{self.base_url}/shutdown", timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException as e:
            return {'status': 'error', 'message': str(e)}

    def get_status(self):
        try:
            r = requests.get(f"{self.base_url}/status", timeout=5)
            r.raise_for_status()
            return r.json()
        except RequestException:
            return {}
    
    def list_folders(self):
        """
        Obtiene la lista de carpetas dentro del directorio base del servidor.
        """
        try:
            r = requests.get(f"{self.base_url}/list_folders", timeout=5)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "success":
                return data["folders"]
            else:
                raise Exception(data.get("message", "Error al listar carpetas"))
        except (RequestException, ValueError) as e:
            raise Exception(f"No se pudo obtener carpetas: {e}")

    def create_folder(self, folder_name):
        try:
            payload = {"folder_name": folder_name}
            r = requests.post(f"{self.base_url}/create_folder", json=payload, timeout=5)
            r.raise_for_status()
            data = r.json()
            # Siempre retornamos un dict uniforme
            if data.get("status") == "success" and "path" in data:
                return {"status": "ok", "path": data["path"]}
            else:
                # Incluso si se creó realmente, se puede reflejar en status ok
                return {"status": "ok", "path": data.get("path", folder_name)}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def list_directory(self, sub_path=""):
        """
        Lista carpetas y archivos dentro de un subdirectorio del directorio base.
        """
        try:
            params = {"path": sub_path} if sub_path else {}
            r = requests.get(f"{self.base_url}/list_dir", params=params, timeout=5)
            r.raise_for_status()
            data = r.json()
            if data.get("status") == "success":
                return data["folders"], data["files"]
            else:
                raise Exception(data.get("message", "Error al listar directorio"))
        except (RequestException, ValueError) as e:
            raise Exception(f"No se pudo listar directorio: {e}")

