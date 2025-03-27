import cv2
from flask import Response
import time

def generate_frames():
    """
    Generator function that captures continuous frames from the camera
    and yields them in MJPEG format for streaming
    """
    # Use the USB webcam at /dev/video0
    camera = cv2.VideoCapture(0)  # 0 corresponds to /dev/video0
    
    # Set camera parameters
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    camera.set(cv2.CAP_PROP_FPS, 24)
    
    # Allow camera to initialize
    time.sleep(1)
    
    try:
        while True:
            # Capture frame-by-frame
            success, frame = camera.read()
            if not success:
                print("Failed to capture frame from camera. Trying again...")
                time.sleep(0.5)
                continue
                
            # Encode the frame in JPEG format
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Failed to encode frame. Trying again...")
                continue
                
            # Convert to bytes
            frame_bytes = buffer.tobytes()
            
            # Yield the frame in the MJPEG format
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
            
            # Small delay to control frame rate
            time.sleep(0.04)  # ~25 fps
    
    finally:
        # Release the camera when the generator is done
        camera.release()
