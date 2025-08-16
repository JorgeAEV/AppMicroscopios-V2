from flask import Flask, Response, jsonify, request, send_file
from camera_manager import CameraManager
from dht_sensor import DHTSensor
from led_control import LedController
from experiment import Experiment
from utils import get_raspberry_status
import threading
import os
from config import BASE_FOLDER_PATH


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

def safe_join(base, *paths):
    """Une rutas de forma segura evitando salir del directorio base."""
    final_path = os.path.abspath(os.path.join(base, *paths))
    if not final_path.startswith(base):
        raise ValueError("Ruta fuera del directorio permitido")
    return final_path

@app.route('/list_folders', methods=['GET'])
def list_folders():
    """
    Lista todas las carpetas dentro del directorio base.
    """
    try:
        folders = [
            f for f in os.listdir(BASE_FOLDER_PATH)
            if os.path.isdir(os.path.join(BASE_FOLDER_PATH, f))
        ]
        return jsonify({"status": "success", "folders": folders})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/create_folder', methods=['POST'])
def create_folder():
    """
    Crea una carpeta nueva dentro del directorio base.
    """
    try:
        data = request.get_json()
        folder_name = data.get("folder_name", "").strip()

        if not folder_name:
            return jsonify({"status": "error", "message": "Nombre de carpeta vacío"}), 400

        if "/" in folder_name or "\\" in folder_name:
            return jsonify({"status": "error", "message": "Nombre de carpeta inválido"}), 400

        folder_path = safe_join(BASE_FOLDER_PATH, folder_name)
        os.makedirs(folder_path, exist_ok=True)

        return jsonify({"status": "success", "message": f"Carpeta '{folder_name}' creada"})
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/list_dir', methods=['GET'])
def list_dir():
    """
    Lista carpetas y archivos dentro de un subdirectorio del directorio base.
    Parámetro opcional: ?path=subcarpeta
    """
    try:
        sub_path = request.args.get("path", "").strip()
        abs_path = safe_join(BASE_FOLDER_PATH, sub_path)

        if not os.path.exists(abs_path):
            return jsonify({"status": "error", "message": "Ruta no encontrada"}), 404

        items = os.listdir(abs_path)
        folders = [f for f in items if os.path.isdir(os.path.join(abs_path, f))]
        files = [f for f in items if os.path.isfile(os.path.join(abs_path, f))]

        return jsonify({"status": "success", "folders": folders, "files": files})
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
