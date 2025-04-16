import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime, timedelta
import time
import RPi.GPIO as GPIO
from sqlalchemy import func, and_
from app import create_app, db
from app.models import SensorReading, SystemSetting
from app.routes import get_system_setting
from app.utils.soil_sensor import SoilSensor

# Set up logging
log_dir = "/var/log/smart-garden"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "control-system.log")

# Configure logger
logger = logging.getLogger("smart-garden-control")
logger.setLevel(logging.INFO)

# Create rotating file handler (10MB max size, keep 5 backup files)
handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class ControlSystem:
    def __init__(self):
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)
        logger.info("Control system initializing...")

        # Define GPIO pins (update with your actual pins)
        self.LIGHT_RELAY_PIN = 17  # LIGHT RELAY
        self.FAN_RELAY_PIN = 18    # FAN RELAY
        self.PUMP_RELAY_PIN = 23   # PUMP RELAY

        # Setup GPIO pins
        self.setup_gpio()
        logger.info(f"GPIO pins configured: Lights={self.LIGHT_RELAY_PIN}, Fan={self.FAN_RELAY_PIN}, Pump={self.PUMP_RELAY_PIN}")

        # Create Flask app context
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        logger.info("Flask app context created")

    def setup_gpio(self):
        """Setup GPIO pins"""
        GPIO.setup(self.LIGHT_RELAY_PIN, GPIO.OUT)
        GPIO.setup(self.FAN_RELAY_PIN, GPIO.OUT)
        GPIO.setup(self.PUMP_RELAY_PIN, GPIO.OUT)
        # Initialize relays to OFF state
        GPIO.output(self.LIGHT_RELAY_PIN, GPIO.LOW)
        GPIO.output(self.FAN_RELAY_PIN, GPIO.LOW)
        GPIO.output(self.PUMP_RELAY_PIN, GPIO.LOW)
        logger.debug("GPIO pins initialized to OFF state")

    def get_average_readings(self, minutes=10):
        """Get average sensor readings for the last X minutes"""
        time_threshold = datetime.utcnow() - timedelta(minutes=minutes)
        logger.debug(f"Getting average readings for past {minutes} minutes")

        results = db.session.query(
            func.avg(SensorReading.temperature).label('avg_temp'),
            func.avg(SensorReading.humidity).label('avg_humidity'),
            func.avg(SensorReading.co2).label('avg_co2'),
            func.avg(SensorReading.moisture).label('avg_moisture')
        ).filter(
            SensorReading.timestamp >= time_threshold
        ).first()
        
        logger.debug(f"Average readings: Temp={results.avg_temp:.1f}, Humidity={results.avg_humidity:.1f}, CO2={results.avg_co2:.1f}, Moisture={results.avg_moisture:.1f}" if results.avg_temp is not None else "No readings available")
        return results

    def should_pump_be_on(self, avg_readings):
        if not avg_readings or avg_readings.avg_moisture is None:
            logger.debug("No moisture readings available, keeping pump off")
            return False

        moisture_min = float(get_system_setting('moisture', 'min', default=30))
        moisture_max = float(get_system_setting('moisture', 'max', default=80))
        
        result = (avg_readings.avg_moisture < moisture_min and 
                avg_readings.avg_moisture < moisture_max)
        
        logger.debug(f"Pump decision: {'ON' if result else 'OFF'} (Current: {avg_readings.avg_moisture:.1f}%, Min: {moisture_min}%, Max: {moisture_max}%)")
        return result

    def should_lights_be_on(self):
        """Check if lights should be on based on schedule"""
        light_on_time = get_system_setting('light', 'on_time', default='06:00')
        light_off_time = get_system_setting('light', 'off_time', default='20:00')
        current_time = datetime.now().strftime('%H:%M')

        if light_on_time <= light_off_time:
            result = light_on_time <= current_time <= light_off_time
        else:
            result = current_time >= light_on_time or current_time <= light_off_time
            
        logger.debug(f"Light schedule decision: {'ON' if result else 'OFF'} (Current: {current_time}, On: {light_on_time}, Off: {light_off_time})")
        return result

    def should_fan_be_on(self, avg_readings):
        """Determine if fan should be on based on any threshold being exceeded"""
        if not avg_readings:
            logger.debug("No readings available, keeping fan off")
            return False

        # Get thresholds from settings
        temp_max = float(get_system_setting('temperature', 'max', default=75))
        humid_max = float(get_system_setting('humidity', 'max', default=80))
        co2_max = float(get_system_setting('co2', 'max', default=1500))

        # Check if any threshold is exceeded
        result = (
            avg_readings.avg_temp > temp_max or
            avg_readings.avg_humidity > humid_max or
            avg_readings.avg_co2 > co2_max
        )
        
        trigger_reason = []
        if avg_readings.avg_temp > temp_max:
            trigger_reason.append(f"Temp {avg_readings.avg_temp:.1f} > {temp_max}")
        if avg_readings.avg_humidity > humid_max:
            trigger_reason.append(f"Humidity {avg_readings.avg_humidity:.1f}% > {humid_max}%")
        if avg_readings.avg_co2 > co2_max:
            trigger_reason.append(f"CO2 {avg_readings.avg_co2:.1f} > {co2_max}")
            
        logger.debug(f"Fan decision: {'ON' if result else 'OFF'}{' - Triggers: ' + ', '.join(trigger_reason) if result else ''}")
        return result

    def control_systems(self):
        """Control lights and fan based on settings and readings"""
        logger.info("Running control systems check...")

        # Get average readings
        avg_readings = self.get_average_readings()

        # Control lights based on schedule
        light_status_before = GPIO.input(self.LIGHT_RELAY_PIN)
        light_should_be_on = self.should_lights_be_on()
        if light_should_be_on:
            GPIO.output(self.LIGHT_RELAY_PIN, GPIO.HIGH)  # Turn on
        else:
            GPIO.output(self.LIGHT_RELAY_PIN, GPIO.LOW)  # Turn off
            
        if light_status_before != GPIO.input(self.LIGHT_RELAY_PIN):
            logger.info(f"Lights turned {'ON' if light_should_be_on else 'OFF'}")

        # Control fan based on readings
        fan_status_before = GPIO.input(self.FAN_RELAY_PIN)
        fan_should_be_on = self.should_fan_be_on(avg_readings)
        if fan_should_be_on:
            GPIO.output(self.FAN_RELAY_PIN, GPIO.HIGH)  # Turn on
        else:
            GPIO.output(self.FAN_RELAY_PIN, GPIO.LOW)  # Turn off
            
        if fan_status_before != GPIO.input(self.FAN_RELAY_PIN):
            logger.info(f"Fan turned {'ON' if fan_should_be_on else 'OFF'}")

        # Control pump based on moisture readings
        pump_status_before = GPIO.input(self.PUMP_RELAY_PIN)
        pump_should_be_on = self.should_pump_be_on(avg_readings)
        if pump_should_be_on:
            GPIO.output(self.PUMP_RELAY_PIN, GPIO.HIGH)
        else:
            GPIO.output(self.PUMP_RELAY_PIN, GPIO.LOW)
            
        if pump_status_before != GPIO.input(self.PUMP_RELAY_PIN):
            logger.info(f"Pump turned {'ON' if pump_should_be_on else 'OFF'}")

    def run(self):
        """Main control loop"""
        logger.info("Control system starting main loop")
        try:
            while True:
                self.control_systems()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            logger.info("Shutting down control system due to keyboard interrupt")
        except Exception as e:
            logger.exception(f"Unexpected error occurred: {str(e)}")
        finally:
            GPIO.cleanup()
            logger.info("GPIO pins cleaned up")
            self.app_context.pop()
            logger.info("App context popped, control system shutdown complete")

if __name__ == '__main__':
    logger.info("=== Control System Service Starting ===")
    control_system = ControlSystem()
    control_system.run()
