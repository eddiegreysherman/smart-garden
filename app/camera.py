import cv2
from flask import Response
import time

class Camera:
    _instance = None
    _camera = None
    _last_access = 0
    _timeout = 10  # Timeout in seconds

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if Camera._instance is not None:
            raise Exception("Camera class is a singleton!")
        self._initialize_camera()

    def _initialize_camera(self):
        if Camera._camera is not None:
            Camera._camera.release()
        
        Camera._camera = cv2.VideoCapture(0, cv2.CAP_V4L2)
        Camera._camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        Camera._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        Camera._camera.set(cv2.CAP_PROP_FPS, 24)
        Camera._camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))
        
        # Allow camera to initialize
        time.sleep(1)
        
        if not Camera._camera.isOpened():
            raise RuntimeError("Could not initialize camera!")

    def get_frame(self):
        Camera._last_access = time.time()
        
        if Camera._camera is None or not Camera._camera.isOpened():
            self._initialize_camera()

        success, frame = Camera._camera.read()
        if not success:
            print("Failed to capture frame from camera. Trying again...")
            time.sleep(0.5)
            return None

        ret, buffer = cv2.imencode('.jpg', frame)
        if not ret:
            print("Failed to encode frame. Trying again...")
            return None

        return buffer.tobytes()

    def cleanup(self):
        if Camera._camera is not None:
            Camera._camera.release()
            Camera._camera = None

    def __del__(self):
        self.cleanup()

def generate_frames():
    """
    Generator function that captures continuous frames from the camera
    and yields them in MJPEG format for streaming
    """
    camera = Camera.get_instance()
    
    try:
        while True:
            frame_bytes = camera.get_frame()
            if frame_bytes is not None:
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
            
            # Small delay to control frame rate
            time.sleep(0.04)  # ~25 fps
            
            # Release camera if not accessed for a while
            if time.time() - Camera._last_access > Camera._timeout:
                camera.cleanup()
                break
    
    except Exception as e:
        print(f"Error in generate_frames: {e}")
        camera.cleanup()
        raise
