#!/usr/bin/env python3
"""
Smart Garden Control System

This module implements the core control system for the Smart Garden project.
It manages the automated control of lights, fans, and water pump based on
sensor readings and user-defined settings.

Key Components:
    - GPIO control for relays (lights, fan, pump)
    - Sensor data processing and averaging
    - Automated decision making for environmental control
    - Logging system for monitoring and debugging

Hardware Requirements:
    - Raspberry Pi with GPIO
    - Relay modules connected to BCM pins:
        - Light Relay: GPIO 17
        - Fan Relay: GPIO 18
        - Pump Relay: GPIO 23
"""

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

# Configure logging system with rotation to manage file sizes
log_dir = "/var/log/smart-garden"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "control-system.log")

logger = logging.getLogger("smart-garden-control")
logger.setLevel(logging.INFO)

# Implement rotating logs: 10MB max size with 5 backup files
handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class ControlSystem:
    """
    Main control system class for managing garden environment.

    This class handles all aspects of the automated garden control including
    sensor monitoring, relay control, and environmental maintenance based
    on user-defined parameters.
    """

    def __init__(self):
        """
        Initialize the control system.

        Sets up GPIO pins, initializes relay states, and creates the Flask
        application context for database access.
        """
        # Initialize GPIO using BCM pin numbering scheme
        GPIO.setmode(GPIO.BCM)
        logger.info("Control system initializing...")

        # Define GPIO pins for relay control
        self.LIGHT_RELAY_PIN = 17  # Controls grow lights
        self.FAN_RELAY_PIN = 18    # Controls ventilation fan
        self.PUMP_RELAY_PIN = 23   # Controls water pump
        self.pump_start_time = None  # Tracks pump operation timing

        self.setup_gpio()
        logger.info(f"GPIO pins configured: Lights={self.LIGHT_RELAY_PIN}, Fan={self.FAN_RELAY_PIN}, Pump={self.PUMP_RELAY_PIN}")

        # Initialize Flask context for database operations
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()
        logger.info("Flask app context created")

    def setup_gpio(self):
        """
        Configure GPIO pins and set initial states.
        
        Sets up all relay pins as outputs and initializes them to OFF state
        for safety on system startup.
        """
        GPIO.setup(self.LIGHT_RELAY_PIN, GPIO.OUT)
        GPIO.setup(self.FAN_RELAY_PIN, GPIO.OUT)
        GPIO.setup(self.PUMP_RELAY_PIN, GPIO.OUT)
        # Initialize all relays to OFF (LOW) state
        GPIO.output(self.LIGHT_RELAY_PIN, GPIO.LOW)
        GPIO.output(self.FAN_RELAY_PIN, GPIO.LOW)
        GPIO.output(self.PUMP_RELAY_PIN, GPIO.LOW)
        logger.debug("GPIO pins initialized to OFF state")

    def get_average_readings(self, minutes=10):
        """
        Calculate average sensor readings over a specified time period.

        Args:
            minutes (int): Time window for averaging readings (default: 10)

        Returns:
            SQLAlchemy Result: Contains averaged sensor values (temperature,
                             humidity, CO2, and moisture)
        """
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
        """
        Determine if the water pump should be active.

        Uses moisture readings and timing logic to control pump operation.
        Implements both moisture threshold and duration-based control.

        Args:
            avg_readings: Averaged sensor data including moisture levels

        Returns:
            bool: True if pump should be running, False otherwise
        """
        if not avg_readings or avg_readings.avg_moisture is None:
            logger.debug("No moisture readings available, keeping pump off")
            return False

        moisture_min = float(get_system_setting('moisture', 'min', default=30))
        pump_duration = float(get_system_setting('moisture', 'pump_duration', default=60))

        pump_is_running = GPIO.input(self.PUMP_RELAY_PIN)
        current_time = time.time()
        
        if pump_is_running:
            # Handle running pump timing logic
            if not hasattr(self, 'pump_start_time') or self.pump_start_time is None:
                logger.warning("Pump is running but no start time recorded, turning off")
                return False
            
            elapsed_time = current_time - self.pump_start_time
            if elapsed_time >= pump_duration:
                logger.info(f"Pump timer expired after {elapsed_time:.1f} seconds")
                self.pump_start_time = None
                return False
            return True
        else:
            # Check if pump should start based on moisture level
            if avg_readings.avg_moisture < moisture_min:
                logger.info(f"Starting pump: moisture {avg_readings.avg_moisture:.1f}% below minimum {moisture_min}%")
                self.pump_start_time = current_time
                return True
            return False

    def should_lights_be_on(self):
        """
        Determine if grow lights should be active based on time schedule.

        Compares current time against user-defined schedule, handling both
        same-day and overnight schedules.

        Returns:
            bool: True if lights should be on, False otherwise
        """
        light_on_time = get_system_setting('light', 'on_time', default='06:00')
        light_off_time = get_system_setting('light', 'off_time', default='20:00')
        current_time = datetime.now().strftime('%H:%M')

        if light_on_time <= light_off_time:
            # Same-day schedule (e.g., 06:00 to 20:00)
            result = light_on_time <= current_time <= light_off_time
        else:
            # Overnight schedule (e.g., 20:00 to 06:00)
            result = current_time >= light_on_time or current_time <= light_off_time
                
        logger.debug(f"Light schedule decision: {'ON' if result else 'OFF'} (Current: {current_time}, On: {light_on_time}, Off: {light_off_time})")
        return result

    def should_fan_be_on(self, avg_readings):
        """
        Determine if ventilation fan should be active.

        Checks multiple environmental factors (temperature, humidity, CO2)
        against their respective thresholds.

        Args:
            avg_readings: Averaged sensor data

        Returns:
            bool: True if fan should be on, False otherwise
        """
        if not avg_readings:
            logger.debug("No readings available, keeping fan off")
            return False

        # Retrieve threshold settings
        temp_max = float(get_system_setting('temperature', 'max', default=75))
        humid_max = float(get_system_setting('humidity', 'max', default=80))
        co2_max = float(get_system_setting('co2', 'max', default=1500))

        # Check all environmental thresholds
        result = (
            avg_readings.avg_temp > temp_max or
            avg_readings.avg_humidity > humid_max or
            avg_readings.avg_co2 > co2_max
        )
        
        # Log specific trigger conditions
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
        """
        Main control loop for managing all garden systems.

        Coordinates the operation of lights, fan, and pump based on
        current conditions and settings. Logs all state changes.
        """
        logger.info("Running control systems check...")

        # Get current environmental readings
        avg_readings = self.get_average_readings()

        # Light control
        light_status_before = GPIO.input(self.LIGHT_RELAY_PIN)
        light_should_be_on = self.should_lights_be_on()
        GPIO.output(self.LIGHT_RELAY_PIN, GPIO.HIGH if light_should_be_on else GPIO.LOW)
                
        if light_status_before != GPIO.input(self.LIGHT_RELAY_PIN):
            logger.info(f"Lights turned {'ON' if light_should_be_on else 'OFF'}")

        # Fan control
        fan_status_before = GPIO.input(self.FAN_RELAY_PIN)
        fan_should_be_on = self.should_fan_be_on(avg_readings)
        GPIO.output(self.FAN_RELAY_PIN, GPIO.HIGH if fan_should_be_on else GPIO.LOW)
                
        if fan_status_before != GPIO.input(self.FAN_RELAY_PIN):
            logger.info(f"Fan turned {'ON' if fan_should_be_on else 'OFF'}")

        # Pump control
        pump_status_before = GPIO.input(self.PUMP_RELAY_PIN)
        pump_should_be_on = self.should_pump_be_on(avg_readings)
        GPIO.output(self.PUMP_RELAY_PIN, GPIO.HIGH if pump_should_be_on else GPIO.LOW)
                
        if pump_status_before != GPIO.input(self.PUMP_RELAY_PIN):
            logger.info(f"Pump turned {'ON' if pump_should_be_on else 'OFF'}")

    def run(self):
        """
        Primary execution loop for the control system.

        Runs continuous monitoring and control loop until interrupted.
        Handles shutdown and cleanup on exit.
        """
        logger.info("Control system starting main loop")
        try:
            while True:
                self.control_systems()
                time.sleep(60)  # Run control check every minute

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
