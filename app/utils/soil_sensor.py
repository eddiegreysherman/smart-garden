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
    """
    A class to interface with a soil moisture sensor connected via serial.
    
    This class provides methods to connect to the sensor, read data,
    and manage the serial connection.
    
    Attributes:
        port (str): The serial port path where the sensor is connected.
        baudrate (int): The baud rate for serial communication.
        serial (serial.Serial): Serial connection object.
        last_reading (float): The most recent moisture reading from the sensor.
    """
    
    def __init__(self, port='/dev/ttyACM0', baudrate=9600):
        """
        Initialize the SoilSensor with connection parameters.
        
        Args:
            port (str, optional): Serial port path. Defaults to '/dev/ttyACM0'.
            baudrate (int, optional): Baud rate for serial communication. Defaults to 9600.
        """
        self.port = port
        self.baudrate = baudrate
        self.serial = None
        self.last_reading = None
    
    def connect(self):
        """
        Establish a connection to the soil moisture sensor.
        
        Attempts to open a serial connection with the specified port and baudrate.
        
        Returns:
            bool: True if connection successful, False otherwise.
        """
        try:
            self.serial = serial.Serial(self.port, self.baudrate, timeout=1)
            logger.info("Successfully connected to soil moisture sensor")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to soil moisture sensor: {e}")
            return False
    
    def read_sensor(self):
        """
        Read the current soil moisture value from the sensor.
        
        Attempts to connect if not already connected, then reads and
        parses JSON data from the serial port.
        
        Returns:
            float: The moisture reading if successful, None otherwise.
        """
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
        """
        Return the most recent moisture reading without reading the sensor.
        
        Returns:
            float: The last moisture reading, could be None if no reading taken yet.
        """
        return self.last_reading
    
    def cleanup(self):
        """
        Close the serial connection to the sensor.
        
        Should be called when the sensor is no longer needed to properly
        release system resources.
        """
        if self.serial:
            self.serial.close()
            logger.info("Closed soil moisture sensor connection")
