import time
import serial
import json
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SoilSensor:
    def __init__(self, port='/dev/ttyACM0', baudrate=9600):
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.last_reading = None

    def connect(self):
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            logger.info("Successfully connected to soil moisture sensor")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to soil moisture sensor: {e}")
            return False

    def read_sensor(self):
        if not self.serial:
            if not self.connect():
                return None

        try:
            if self.serial.in_waiting:
                line = self.serial.readline().decode('utf-8').strip()
                data = json.loads(line)
                self.last_reading = data.get('moisture')
                logger.debug(f"Read moisture value: {self.last_reading}")
                return self.last_reading
        except Exception as e:
            logger.error(f"Error reading soil moisture sensor: {e}")
            return None

    def get_last_reading(self):
        return self.last_reading

    def cleanup(self):
        if self.serial:
            self.serial.close()
            logger.info("Closed soil moisture sensor connection")
