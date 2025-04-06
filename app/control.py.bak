from datetime import datetime, timedelta
import time
import RPi.GPIO as GPIO
from sqlalchemy import func, and_
from app import create_app, db
from app.models import SensorReading, SystemSetting
from app.routes import get_system_setting
from app.utils.soil_sensor import SoilSensor

class ControlSystem:
    def __init__(self):
        # Initialize GPIO
        GPIO.setmode(GPIO.BCM)

        # Define GPIO pins (update with your actual pins)
        self.LIGHT_RELAY_PIN = 17  # LIGHT RELAY
        self.FAN_RELAY_PIN = 18    # FAN RELAY
        self.PUMP_RELAY_PIN = 23   # PUMP RELAY

        # Setup GPIO pins
        self.setup_gpio()

        # Create Flask app context
        self.app = create_app()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def setup_gpio(self):
        """Setup GPIO pins"""
        GPIO.setup(self.LIGHT_RELAY_PIN, GPIO.OUT)
        GPIO.setup(self.FAN_RELAY_PIN, GPIO.OUT)
        GPIO.setup(self.PUMP_RELAY_PIN, GPIO.OUT)
        # Initialize relays to OFF state
        GPIO.output(self.LIGHT_RELAY_PIN, GPIO.LOW)
        GPIO.output(self.FAN_RELAY_PIN, GPIO.LOW)
        GPIO.output(self.PUMP_RELAY_PIN, GPIO.LOW)

    def get_average_readings(self, minutes=10):
        """Get average sensor readings for the last X minutes"""
        time_threshold = datetime.utcnow() - timedelta(minutes=minutes)

        return db.session.query(
            func.avg(SensorReading.temperature).label('avg_temp'),
            func.avg(SensorReading.humidity).label('avg_humidity'),
            func.avg(SensorReading.co2).label('avg_co2'),
            func.avg(SensorReading.moisture).label('avg_moisture')
        ).filter(
            SensorReading.timestamp >= time_threshold
        ).first()

    def should_pump_be_on(self, avg_readings):
    	if not avg_readings or avg_readings.avg_moisture is None:
        	return False

    	moisture_min = float(get_system_setting('moisture', 'min', default=30))
    	moisture_max = float(get_system_setting('moisture', 'max', default=80))
    
    	return (avg_readings.avg_moisture < moisture_min and 
           	avg_readings.avg_moisture < moisture_max)

    def should_lights_be_on(self):
        """Check if lights should be on based on schedule"""
        light_on_time = get_system_setting('light', 'on_time', default='06:00')
        light_off_time = get_system_setting('light', 'off_time', default='20:00')
        current_time = datetime.now().strftime('%H:%M')

        if light_on_time <= light_off_time:
            return light_on_time <= current_time <= light_off_time
        return current_time >= light_on_time or current_time <= light_off_time

    def should_fan_be_on(self, avg_readings):
        """Determine if fan should be on based on any threshold being exceeded"""
        if not avg_readings:
            return False

        # Get thresholds from settings
        temp_max = float(get_system_setting('temperature', 'max', default=75))
        humid_max = float(get_system_setting('humidity', 'max', default=80))
        co2_max = float(get_system_setting('co2', 'max', default=1500))

        # Check if any threshold is exceeded
        return (
            avg_readings.avg_temp > temp_max or
            avg_readings.avg_humidity > humid_max or
            avg_readings.avg_co2 > co2_max
        )

    def control_systems(self):
        """Control lights and fan based on settings and readings"""

        # Get average readings
        avg_readings = self.get_average_readings()

        # Control lights based on schedule
        if self.should_lights_be_on():
            GPIO.output(self.LIGHT_RELAY_PIN, GPIO.HIGH)  # Turn on
        else:
            GPIO.output(self.LIGHT_RELAY_PIN, GPIO.LOW)  # Turn off

        # Control fan based on readings
        if self.should_fan_be_on(avg_readings):
            GPIO.output(self.FAN_RELAY_PIN, GPIO.HIGH)  # Turn on
        else:
            GPIO.output(self.FAN_RELAY_PIN, GPIO.LOW)  # Turn off

        # Control pump based on moisture readings
        if self.should_pump_be_on(avg_readings):
            GPIO.output(self.PUMP_RELAY_PIN, GPIO.HIGH)
        else:
            GPIO.output(self.PUMP_RELAY_PIN, GPIO.LOW)

    def run(self):
        """Main control loop"""
        try:
            while True:
                self.control_systems()
                time.sleep(60)  # Check every minute

        except KeyboardInterrupt:
            print("Shutting down control system...")
        finally:
            GPIO.cleanup()
            self.app_context.pop()

if __name__ == '__main__':
    control_system = ControlSystem()
    control_system.run()
