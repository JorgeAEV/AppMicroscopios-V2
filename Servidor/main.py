from flask import Flask, Response, jsonify, request, send_file
from camera_manager import CameraManager
from dht_sensor import DHTSensor
from led_control import LedController
from experiment import Experiment
from utils import get_raspberry_status
import threading
import os

app = Flask(__name__)

# Configuración de los GPIO usados por cada cámara
CAMERA_LED_PIN_MAP = {
    0: 17,  # GPIO 17 para cámara 0
    1: 27,  # GPIO 27 para cámara 1
    # Agrega más
}

camera_manager = CameraManager()
led_controller = LedController(CAMERA_LED_PIN_MAP)
dht_sensor = DHTSensor(pin=4)  # pin  del DHT11
dht_sensor.start()

experiment = Experiment(camera_manager, led_controller, dht_sensor)

@app.route('/cameras')
def cameras():
    return jsonify(camera_manager.cameras)

@app.route('/video_feed/<int:cam_id>')
def video_feed(cam_id):
    if cam_id not in camera_manager.cameras:
        return "Camera not found", 404
    return Response(camera_manager.generate_frames(cam_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/led/<int:cam_id>/<string:action>', methods=['POST'])
def led_control(cam_id, action):
    if cam_id not in camera_manager.cameras:
        return jsonify({'status': 'error', 'message': 'Camara no encontrada'}), 404
    if action == 'on':
        led_controller.on(cam_id)
    elif action == 'off':
        led_controller.off(cam_id)
    else:
        return jsonify({'status': 'error', 'message': 'Accion no valida'}), 400
    return jsonify({'status': 'ok'})

@app.route('/sensor')
def sensor_data():
    data = dht_sensor.get_readings()
    return jsonify(data)

@app.route('/experiment/start', methods=['POST'])
def start_experiment():
    data = request.json
    save_path = data.get('save_path')
    duration = data.get('duration')
    interval = data.get('interval')
    if not all([save_path, duration, interval]):
        return jsonify({'status': 'error', 'message': 'Faltan parámetros'}), 400
    try:
        experiment.start(save_path, duration, interval)
        return jsonify({'status': 'ok'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/experiment/stop', methods=['POST'])
def stop_experiment():
    experiment.stop()
    return jsonify({'status': 'ok'})

@app.route('/status')
def status():
    status_info = get_raspberry_status()
    return jsonify(status_info)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    """
    Opcional: endpoint para apagar el servidor y limpiar GPIO.
    """
    def shutdown_server():
        led_controller.cleanup()
        camera_manager.release()
        dht_sensor.stop()
        func = request.environ.get('werkzeug.server.shutdown')
        if func:
            func()

    threading.Thread(target=shutdown_server).start()
    return "Shutting down...", 200

@app.route("/list_folders", methods=["GET"])
def list_folders():
    base_path = "/home/pi/experimentos"
    os.makedirs(base_path, exist_ok=True)
    folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
    return jsonify(folders)

@app.route("/create_folder", methods=["POST"])
def create_folder():
    base_path = "/home/pi/experimentos"
    data = request.json
    folder_name = data.get("name")
    if not folder_name:
        return jsonify({"error": "No folder name provided"}), 400
    target_path = os.path.join(base_path, folder_name)
    os.makedirs(target_path, exist_ok=True)
    return jsonify({"path": target_path})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
