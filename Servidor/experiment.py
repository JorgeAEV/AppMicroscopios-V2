# experiment.py
import threading
import time
import os
from datetime import datetime
import cv2

from led_control import turn_on_led, turn_off_led
from Servidor.dht_sensor import read_dht
from Servidor.camera_manager import cameras, capture_frame
from utils import create_experiment_dirs, save_image_with_timestamp

experiment_thread = None
experiment_running = False

def run_experiment(save_path, duration_sec, interval_sec):
    global experiment_running
    experiment_running = True
    start_time = time.time()
    end_time = start_time + duration_sec

    paths = create_experiment_dirs(save_path, cameras)

    while time.time() < end_time and experiment_running:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        dht_data = read_dht()

        for cam in cameras:
            turn_on_led(cam)
            time.sleep(0.2)  # Pequeño delay para iluminación

            frame = capture_frame(cam)
            if frame is not None:
                save_image_with_timestamp(frame, paths[cam], timestamp)

            turn_off_led(cam)

        # Guardar DHT11 (puede guardarse como JSON si se desea)
        with open(os.path.join(save_path, f"dht_{timestamp}.txt"), "w") as f:
            f.write(str(dht_data))

        time.sleep(interval_sec)

    experiment_running = False

def start_experiment_thread(save_path, duration_sec, interval_sec):
    global experiment_thread
    experiment_thread = threading.Thread(
        target=run_experiment,
        args=(save_path, duration_sec, interval_sec),
        daemon=True
    )
    experiment_thread.start()

def stop_experiment():
    global experiment_running
    experiment_running = False
