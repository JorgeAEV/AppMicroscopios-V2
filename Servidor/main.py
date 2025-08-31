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
    # Devuelve lista de IDs de cámaras detectadas
    return jsonify(camera_manager.cameras)

@app.route('/video_feed/<int:cam_id>')
def video_feed(cam_id):
    if cam_id not in camera_manager.cameras:
        return "Camera not found", 404
    return Response(
        camera_manager.generate_frames(cam_id),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# ==============================
#         LEDs: ON/OFF
# ==============================
@app.route('/led/<int:cam_id>/<string:action>', methods=['POST'])
def led_control_endpoint(cam_id, action):
    if cam_id not in camera_manager.cameras:
        return jsonify({'status': 'error', 'message': 'Cámara no encontrada'}), 404
    if action == 'on':
        led_controller.on(cam_id)
    elif action == 'off':
        led_controller.off(cam_id)
    else:
        return jsonify({'status': 'error', 'message': 'Acción no válida'}), 400
    return jsonify({'status': 'ok'})

@app.route('/led/all/<string:action>', methods=['POST'])
def led_control_all_endpoint(action):
    if action == 'on':
        led_controller.all_on()
    elif action == 'off':
        led_controller.all_off()
    else:
        return jsonify({'status': 'error', 'message': 'Acción no válida'}), 400
    return jsonify({'status': 'ok'})

# ==============================
#      LEDs: BRIGHTNESS API
# ==============================
@app.route('/led/<int:cam_id>/brightness', methods=['GET'])
def get_led_brightness(cam_id):
    if cam_id not in camera_manager.cameras:
        return jsonify({'status': 'error', 'message': 'Cámara no encontrada'}), 404
    try:
        val = led_controller.get_brightness(cam_id)
        return jsonify({'status': 'ok', 'value': val})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/led/<int:cam_id>/brightness', methods=['POST'])
def set_led_brightness(cam_id):
    if cam_id not in camera_manager.cameras:
        return jsonify({'status': 'error', 'message': 'Cámara no encontrada'}), 404
    data = request.get_json(silent=True) or {}
    if 'value' not in data:
        return jsonify({'status': 'error', 'message': 'Falta value'}), 400
    try:
        val = int(data['value'])
        led_controller.set_brightness(cam_id, val)
        # No encendemos automáticamente; si está encendido, cambiará duty.
        return jsonify({'status': 'ok', 'value': led_controller.get_brightness(cam_id)})
    except ValueError as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': f'No se pudo ajustar brillo: {e}'}), 500

@app.route('/led/brightness_map', methods=['GET'])
def get_led_brightness_map():
    try:
        # Devuelve el brillo de todas las cámaras con LED mapeado
        result = {}
        for cam_id in CAMERA_LED_PIN_MAP.keys():
            try:
                result[cam_id] = led_controller.get_brightness(cam_id)
            except Exception:
                result[cam_id] = None
        return jsonify({'status': 'ok', 'values': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# ==============================
#        SENSOR: DHT11
# ==============================
@app.route('/sensor')
def sensor_data():
    data = dht_sensor.read()  # Lectura puntual bajo demanda
    return jsonify(data)

# ==============================
#        EXPERIMENTO
# ==============================
@app.route('/experiment/start', methods=['POST'])
def start_experiment():
    data = request.get_json(silent=True) or {}
    save_path = data.get('save_path')  # Ruta relativa al directorio base
    duration = data.get('duration')
    interval = data.get('interval')
    camera_ids = data.get('camera_ids')  # opcional: lista de enteros

    if not all([save_path, duration, interval]):
        return jsonify({'status': 'error', 'message': 'Faltan parámetros'}), 400

    # Normaliza tipos
    try:
        duration = int(duration)
        interval = int(interval)
    except Exception:
        return jsonify({'status': 'error', 'message': 'duration/interval deben ser enteros'}), 400

    # Normaliza camera_ids (puede venir None, lista vacía, lista de strings/ints)
    selected_ids = None
    if camera_ids not in (None, [], ()):
        try:
            detected = set(camera_manager.cameras)
            selected_ids = sorted({int(c) for c in camera_ids if int(c) in detected})
            if not selected_ids:
                selected_ids = None  # si la lista no tiene válidos, caerá en "todas"
        except Exception:
            return jsonify({'status': 'error', 'message': 'camera_ids inválidos'}), 400

    try:
        abs_save_path = safe_join(BASE_FOLDER_PATH, save_path)
        os.makedirs(abs_save_path, exist_ok=True)
        # Pasa lista (o None) al experimento
        experiment.start(abs_save_path, duration, interval, camera_ids=selected_ids)
        return jsonify({
            'status': 'ok',
            'save_path': abs_save_path,
            'camera_ids': experiment.camera_ids  # confirma cuáles se usarán realmente
        })
    except ValueError as ve:
        return jsonify({'status': 'error', 'message': str(ve)}), 400
    except PermissionError:
        return jsonify({
            'status': 'error',
            'message': f'Sin permisos para crear/escribir en: {abs_save_path}'
        }), 403
    except RuntimeError as re:
        # p.ej. "Experimento ya en ejecución"
        return jsonify({'status': 'error', 'message': str(re)}), 409
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/experiment/stop', methods=['POST'])
def stop_experiment():
    experiment.stop()
    return jsonify({'status': 'ok'})

# ==============================
#           STATUS
# ==============================
@app.route('/status')
def status():
    """
    Estado del sistema y del experimento en curso.
    Incluye qué cámaras participan y el brillo por cámara.
    """
    sys_info = get_raspberry_status()
    # Mapa de brillos actual (si alguna cámara no tiene LED, puede no estar presente)
    led_map = {}
    for cam_id in CAMERA_LED_PIN_MAP.keys():
        try:
            led_map[cam_id] = led_controller.get_brightness(cam_id)
        except Exception:
            led_map[cam_id] = None

    exp_info = {
        'running': experiment.running,
        'save_path': experiment.save_path,
        'duration': experiment.duration,
        'interval': experiment.interval,
        'camera_ids': experiment.camera_ids,  # subconjunto activo (o todas)
        'led_brightness': led_map
    }
    return jsonify({'system': sys_info, 'experiment': exp_info})

# ==============================
#          SHUTDOWN
# ==============================
@app.route('/shutdown', methods=['POST'])
def shutdown():
    """
    Endpoint para apagar el servidor y limpiar GPIO.
    """
    def shutdown_server():
        try:
            led_controller.cleanup()
        except Exception:
            pass
        try:
            camera_manager.release()
        except Exception:
            pass
        try:
            dht_sensor.cleanup()  # cleanup en lugar de stop
        except Exception:
            pass
        func = request.environ.get('werkzeug.server.shutdown')
        if func:
            func()

    threading.Thread(target=shutdown_server, daemon=True).start()
    return jsonify({'status': 'ok', 'message': 'Shutting down...'}), 200

# ==============================
#         UTILIDADES
# ==============================
def safe_join(base, *paths):
    """Une rutas de forma segura evitando salir del directorio base."""
    normalized_paths = [p.replace('\\', '/') for p in paths]
    final_path = os.path.abspath(os.path.join(base, *normalized_paths))
    if not final_path.startswith(os.path.abspath(base)):
        raise ValueError("Ruta fuera del directorio permitido")
    return final_path

# ==============================
#       FS: LISTAR/CREAR
# ==============================
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

# ==============================
#            RUN
# ==============================
if __name__ == '__main__':
    # threaded=True permite múltiples requests (stream + control) sin bloquear
    app.run(host='0.0.0.0', port=5000, threaded=True)
