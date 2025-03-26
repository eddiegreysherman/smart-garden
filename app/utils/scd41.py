import time
import board
import adafruit_scd4x
import logging
from app.models import SensorReading
from app import create_app, db
app = create_app()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Push an application context
app.app_context().push()

try:
    i2c = board.I2C()
    scd4x = adafruit_scd4x.SCD4X(i2c)
    logger.info("Serial number: %s", [hex(i) for i in scd4x.serial_number])

    scd4x.start_periodic_measurement()
    logger.info("Waiting for first measurement....")

    while True:
        try:
            if scd4x.data_ready:
                co2 = scd4x.CO2
                temperature = scd4x.temperature * (9 / 5) + 32
                humidity = scd4x.relative_humidity

                reading = SensorReading(
                    co2=co2,
                    temperature=temperature,
                    humidity=humidity
                )
                db.session.add(reading)
                db.session.commit()

                logger.info(
                    "Reading: CO2=%d ppm, Temperature=%.1f°F, Humidity=%.1f%%",
                    co2, temperature, humidity
                )
            time.sleep(30)
        except Exception as e:
            logger.error("Error during measurement: %s", str(e))
            db.session.rollback()  # Rollback the database session on error
            time.sleep(5)  # Wait a bit before retrying
except Exception as e:
    logger.error("Fatal error: %s", str(e))
    raise
