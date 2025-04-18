#!/usr/bin/env python3
"""
Sensor Monitoring Script

A background process that continuously reads data from environmental sensors 
and stores readings in the database for the smart garden system.
"""

import time
import board
import adafruit_scd4x
import logging
from app.models import SensorReading
from app import create_app, db
from app.utils.soil_sensor import SoilSensor

# Initialize the Flask application
app = create_app()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Push an application context
# This is required to use Flask's database functions outside of a request context
app.app_context().push()

try:
    # Initialize SCD41 sensor
    # The SCD41 is a high-precision CO2, temperature, and humidity sensor
    i2c = board.I2C()  # Create I2C interface object
    scd4x = adafruit_scd4x.SCD4X(i2c)  # Initialize sensor using the I2C interface
    logger.info("Serial number: %s", [hex(i) for i in scd4x.serial_number])  # Log the sensor's serial number for debugging
    
    # Initialize soil moisture sensor
    # This is a custom sensor implementation from the app's utilities
    soil_sensor = SoilSensor()
    if not soil_sensor.connect():
        logger.error("Failed to initialize soil moisture sensor")
    
    # Start continuous measurement mode on the SCD41 sensor
    scd4x.start_periodic_measurement()
    logger.info("Waiting for first measurement....")
    
    # Main monitoring loop
    while True:
        try:
            if scd4x.data_ready:
                # Read SCD41 sensor data when new data is available
                co2 = scd4x.CO2  # Carbon dioxide level in parts per million (ppm)
                temperature = scd4x.temperature * (9 / 5) + 32  # Convert temperature from Celsius to Fahrenheit
                humidity = scd4x.relative_humidity  # Relative humidity percentage
                
                # Read soil moisture sensor
                # Returns a percentage value representing soil moisture content
                moisture = soil_sensor.read_sensor()
                
                # Create new reading with all sensor data and store in database
                reading = SensorReading(
                    co2=co2,
                    temperature=temperature,
                    humidity=humidity,
                    moisture=moisture
                )
                db.session.add(reading)  # Add the new reading to the database session
                db.session.commit()  # Commit the transaction to permanently store the reading
                
                # Log the measurements for monitoring and debugging
                logger.info(
                    "Reading: CO2=%d ppm, Temperature=%.1f°F, Humidity=%.1f%%, Moisture=%s",
                    co2, temperature, humidity, moisture if moisture is not None else "N/A"
                )
            
            # Wait 30 seconds before taking the next reading
            # This helps avoid excessive database writes and allows sensors time to stabilize
            time.sleep(30)
            
        except Exception as e:
            # Error handling for individual measurements
            # This prevents the entire monitoring process from crashing if a single reading fails
            logger.error("Error during measurement: %s", str(e))
            db.session.rollback()  # Rollback the database session on error to prevent partial commits
            time.sleep(5)  # Wait a bit before retrying to avoid rapid error loops
            
except Exception as e:
    # Top-level error handling for fatal errors that break out of the main loop
    logger.error("Fatal error: %s", str(e))
    
    # Clean up resources if the soil sensor was initialized
    if 'soil_sensor' in locals():
        soil_sensor.cleanup()
        
    # Re-raise the exception to signal the error to the process manager
    raise
