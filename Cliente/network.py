# network.py
import requests
from config import BASE_URL

def get_cameras():
    return requests.get(f"{BASE_URL}/cameras").json()

def set_camera(cam_id):
    return requests.post(f"{BASE_URL}/set_camera", json={"camera_id": cam_id})

def start_experiment(path, duration, interval):
    return requests.post(f"{BASE_URL}/start_experiment", json={
        "path": path,
        "duration": duration,
        "interval": interval
    })

def stop_experiment():
    return requests.post(f"{BASE_URL}/stop_experiment")
