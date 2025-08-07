# utils.py
import os
import cv2

def create_experiment_dirs(base_path, camera_ids):
    paths = {}
    os.makedirs(base_path, exist_ok=True)
    for cam in camera_ids:
        cam_path = os.path.join(base_path, f"Microscopio{cam}")
        os.makedirs(cam_path, exist_ok=True)
        paths[cam] = cam_path
    return paths

def save_image_with_timestamp(frame, path, timestamp):
    filename = f"{timestamp}.jpg"
    cv2.imwrite(os.path.join(path, filename), frame)
