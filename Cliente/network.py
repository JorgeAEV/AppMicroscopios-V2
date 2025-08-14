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
        return requests.get(f"{self.base_url}/list_folders").json()

    def create_folder(self, name):
        return requests.post(f"{self.base_url}/create_folder", json={"name": name}).json()

