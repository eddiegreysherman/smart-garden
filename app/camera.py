import cv2
from flask import Response
import time

class Camera:
    """
    Singleton class to manage camera resources efficiently.
    Provides access to the camera for capturing frames and handles proper resource cleanup.
    """
    _instance = None  # Class variable to hold the singleton instance
    _camera = None    # Class variable to hold the camera object
    _last_access = 0  # Timestamp of the last camera access
    _timeout = 10     # Timeout in seconds to auto-release camera when idle
    
    @classmethod
    def get_instance(cls):
        """
        Implements the singleton pattern - returns existing instance or creates a new one.
        
        Returns:
            Camera: The singleton Camera instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """
        Constructor that enforces the singleton pattern and initializes the camera.
        Raises an exception if attempting to create a second instance.
        """
        if Camera._instance is not None:
            raise Exception("Camera class is a singleton!")
        self._initialize_camera()
    
    def _initialize_camera(self):
        """
        Sets up the camera with specific configuration parameters.
        Releases any existing camera connection before creating a new one.
        Configures resolution, framerate, and video format.
        """
        if Camera._camera is not None:
            Camera._camera.release()
        
        Camera._camera = cv2.VideoCapture(0, cv2.CAP_V4L2)  # Open camera using Video4Linux2 API
        Camera._camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)   # Set frame width
        Camera._camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set frame height
        Camera._camera.set(cv2.CAP_PROP_FPS, 24)            # Set frames per second
        Camera._camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M','J','P','G'))  # Set MJPEG format
        
        # Allow camera to initialize
        time.sleep(1)
        
        if not Camera._camera.isOpened():
            raise RuntimeError("Could not initialize camera!")
    
    def get_frame(self):
        """
        Captures a frame from the camera and returns it as JPEG-encoded bytes.
        Updates last access timestamp for timeout tracking.
        Handles camera errors by reinitializing when needed.
        
        Returns:
            bytes: JPEG-encoded image data or None if capture failed
        """
        Camera._last_access = time.time()
        
        if Camera._camera is None or not Camera._camera.isOpened():
            self._initialize_camera()
        
        success, frame = Camera._camera.read()  # Capture frame
        if not success:
            print("Failed to capture frame from camera. Trying again...")
            time.sleep(0.5)
            return None
        
        ret, buffer = cv2.imencode('.jpg', frame)  # Encode to JPEG format
        if not ret:
            print("Failed to encode frame. Trying again...")
            return None
        
        return buffer.tobytes()  # Convert to bytes for HTTP streaming
    
    def cleanup(self):
        """
        Releases camera resources to free them for other processes.
        Should be called when camera is not needed anymore.
        """
        if Camera._camera is not None:
            Camera._camera.release()
            Camera._camera = None
    
    def __del__(self):
        """
        Destructor that ensures camera resources are released when the object is garbage collected.
        """
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
                # Format the frame as part of an MJPEG stream (multipart HTTP response)
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
