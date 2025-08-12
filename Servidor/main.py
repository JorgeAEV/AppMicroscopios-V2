# main.py
from flask import Flask, request, jsonify, Response
from camera_manager import detect_cameras, generate_frames, set_camera, get_current_camera, cameras
from experiment import start_experiment_thread, stop_experiment
import os

app = Flask(__name__)
detect_cameras()

@app.route('/cameras')
def list_cameras():
    return jsonify(cameras)

@app.route('/set_camera', methods=['POST'])
def change_camera():
    cam_id = request.json.get('camera_id')
    if set_camera(cam_id):
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'error', 'message': 'Camera not found'}), 400

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/start_experiment', methods=['POST'])
def start_experiment():
    data = request.json
    path = data.get('path')
    duration = int(data.get('duration'))  # seconds
    interval = int(data.get('interval'))  # seconds
    if not all([path, duration, interval]):
        return jsonify({'status': 'error', 'message': 'Missing parameters'}), 400
    os.makedirs(path, exist_ok=True)
    start_experiment_thread(path, duration, interval)
    return jsonify({'status': 'started'})

@app.route('/stop_experiment', methods=['POST'])
def stop_experiment_route():
    stop_experiment()
    return jsonify({'status': 'stopped'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
