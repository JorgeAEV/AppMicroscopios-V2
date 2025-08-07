# video_thread.py
from PyQt6.QtCore import QThread, pyqtSignal
import requests
import numpy as np
import cv2

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self._run_flag = True

    def run(self):
        stream = requests.get(self.url, stream=True)
        bytes_data = b''
        for chunk in stream.iter_content(chunk_size=1024):
            if not self._run_flag:
                break
            bytes_data += chunk
            a = bytes_data.find(b'\xff\xd8')
            b = bytes_data.find(b'\xff\xd9')
            if a != -1 and b != -1:
                jpg = bytes_data[a:b+2]
                bytes_data = bytes_data[b+2:]
                img = cv2.imdecode(np.frombuffer(jpg, dtype=np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    self.change_pixmap_signal.emit(img)

    def stop(self):
        self._run_flag = False
        self.wait()
