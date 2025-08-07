# camera_manager.py
import cv2
import threading

MAX_CAMERAS = 4
cameras = []
current_cam_index = 0
lock = threading.Lock()

def detect_cameras():
    global cameras
    cameras = []
    for i in range(MAX_CAMERAS):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            cameras.append(i)
            cap.release()
    return cameras

def set_camera(index):
    global current_cam_index
    if index in cameras:
        with lock:
            current_cam_index = index
        return True
    return False

def get_current_camera():
    return current_cam_index

def generate_frames():
    cap = cv2.VideoCapture(get_current_camera())
    while True:
        with lock:
            ret, frame = cap.read()
        if not ret:
            continue
        _, buffer = cv2.imencode('.jpg', frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

def capture_frame(index):
    cap = cv2.VideoCapture(index)
    ret, frame = cap.read()
    cap.release()
    return frame if ret else None
