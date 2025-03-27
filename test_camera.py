import picamera
import time

try:
    print("Initializing camera...")
    with picamera.PiCamera() as camera:
        print("Camera initialized successfully!")
        camera.resolution = (640, 480)
        print("Taking 2 second preview...")
        time.sleep(2)
        print("Done!")
except Exception as e:
    print(f"Error: {e}")
