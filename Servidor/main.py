# main.py
from flask import Flask, Response, jsonify, request
from camera_manager import CameraManager
from led_control import LedController
from experiment import Experiment
from utils import get_raspberry_status
from config import BASE_FOLDER_PATH
from dht_sensor import DHTSensor
import threading
import os

app = Flask(__name__)

# Configuración de los GPIO usados por cada cámara
CAMERA_LED_PIN_MAP = {
    0: 17,  # GPIO 17 para cámara 0
    1: 27,  # GPIO 27 para cámara 1
    # Agrega más según sea necesario
}

# Configuración del pin BCM para el DHT11
DHT11_PIN = 4  # GPIO4 en modo BCM

camera_manager = CameraManager()
led_controller = LedController(CAMERA_LED_PIN_MAP)
dht_sensor = DHTSensor(pin=DHT11_PIN)  # Nuevo diseño: solo número de pin BCM

experiment = Experiment(camera_manager, led_controller, dht_sensor)

@app.route('/cameras')
def cameras():
    return jsonify(camera_manager.cameras)

@app.route('/video_feed/<int:cam_id>')
def video_feed(cam_id):
    if cam_id not in camera_manager.cameras:
        return "Camera not found", 404
    return Response(
        camera_manager.generate_frames(cam_id),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/led/<int:cam_id>/<string:action>', methods=['POST'])
def led_control(cam_id, action):
    if cam_id not in camera_manager.cameras:
        return jsonify({'status': 'error', 'message': 'Cámara no encontrada'}), 404
    if action == 'on':
        led_controller.on(cam_id)
    elif action == 'off':
        led_controller.off(cam_id)
    else:
        return jsonify({'status': 'error', 'message': 'Acción no válida'}), 400
    return jsonify({'status': 'ok'})

@app.route('/sensor')
def sensor_data():
    data = dht_sensor.read()  # Nuevo: lectura puntual bajo demanda
    return jsonify(data)

@app.route('/experiment/start', methods=['POST'])
def start_experiment():
    data = request.json
    save_path = data.get('save_path')  # Ruta relativa al directorio base
    duration = data.get('duration')
    interval = data.get('interval')
    
    if not all([save_path, duration, interval]):
        return jsonify({'status': 'error', 'message': 'Faltan parámetros'}), 400
    
    try:
        abs_save_path = safe_join(BASE_FOLDER_PATH, save_path)
        os.makedirs(abs_save_path, exist_ok=True)
        experiment.start(abs_save_path, duration, interval)
        return jsonify({'status': 'ok'})
    except ValueError as ve:
        return jsonify({'status': 'error', 'message': str(ve)}), 400
    except PermissionError:
        return jsonify({
            'status': 'error', 
            'message': f'Sin permisos para crear/escribir en: {abs_save_path}'
        }), 403
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
    Endpoint para apagar el servidor y limpiar GPIO.
    """
    def shutdown_server():
        led_controller.cleanup()
        camera_manager.release()
        dht_sensor.cleanup()  # Nuevo: cleanup en lugar de stop
        func = request.environ.get('werkzeug.server.shutdown')
        if func:
            func()

    threading.Thread(target=shutdown_server, daemon=True).start()
    return jsonify({'status': 'ok', 'message': 'Shutting down...'}), 200

def safe_join(base, *paths):
    """Une rutas de forma segura evitando salir del directorio base."""
    normalized_paths = [p.replace('\\', '/') for p in paths]
    final_path = os.path.abspath(os.path.join(base, *normalized_paths))
    if not final_path.startswith(os.path.abspath(base)):
        raise ValueError("Ruta fuera del directorio permitido")
    return final_path

@app.route('/list_dir', methods=['GET'])
def list_dir():
    try:
        sub_path = request.args.get("path", "").strip()
        sub_path = sub_path.replace('\\', '/')
        abs_path = safe_join(BASE_FOLDER_PATH, sub_path)

        if not os.path.exists(abs_path):
            return jsonify({"status": "error", "message": "Ruta no encontrada"}), 404

        items = os.listdir(abs_path)
        folders = [f for f in items if os.path.isdir(os.path.join(abs_path, f))]
        files = [f for f in items if os.path.isfile(os.path.join(abs_path, f))]
        parent_path = os.path.dirname(sub_path) if sub_path else ""
        
        return jsonify({
            "status": "success",
            "current_path": sub_path,
            "parent_path": parent_path,
            "folders": folders,
            "files": files
        })
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/create_folder', methods=['POST'])
def create_folder():
    try:
        data = request.get_json()
        folder_path = data.get("folder_path", "").strip()
        folder_path = folder_path.replace('\\', '/')

        if not folder_path:
            return jsonify({"status": "error", "message": "Ruta de carpeta vacía"}), 400

        try:
            abs_path = safe_join(BASE_FOLDER_PATH, folder_path)
        except ValueError as ve:
            return jsonify({"status": "error", "message": str(ve)}), 400

        try:
            os.makedirs(abs_path, exist_ok=True)
            return jsonify({
                "status": "success", 
                "message": f"Ruta creada: {folder_path}",
                "path": folder_path
            })
        except PermissionError:
            return jsonify({
                "status": "error",
                "message": f"Sin permisos para crear: {abs_path}"
            }), 403
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error creando carpetas: {str(e)}"
            }), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
