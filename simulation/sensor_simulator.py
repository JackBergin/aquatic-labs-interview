"""
sensor_simulator.py
Simulates 3 water quality sensors sending temperature and conductivity measurements.
Sends data to http://localhost:8081/measurements every 5 seconds.
Usage:
python sensor_simulator.py
Requirements:
pip install requests
"""

import requests
import time
import random
from datetime import datetime
from utils.logger_config import setup_logging
from utils.config import (
    API_URL,
    SENSORS,
    INTERVAL_SECONDS,
    TEMP_RANGE,
    CONDUCTIVITY_RANGE,
)

logger = setup_logging("simulation")


def generate_measurement(sensor_id):
    """Generate a realistic sensor measurement."""
    return {
        "sensor_id": sensor_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "temperature": round(random.uniform(*TEMP_RANGE), 1),
        "conductivity": random.randint(*CONDUCTIVITY_RANGE),
    }


def send_measurement(measurement):
    """Send measurement to the API endpoint."""
    try:
        response = requests.post(API_URL, json=measurement, timeout=5)
        if response.status_code == 201:
            logger.info(
                f"Sent: {measurement['sensor_id']} -"
                f"Temp: {measurement['temperature']}°C, "
                f"Cond: {measurement['conductivity']} µS/cm"
            )
        else:
            logger.info(f"Error {response.status_code}: {measurement['sensor_id']}")
    except requests.exceptions.ConnectionError:
        logger.error(
            f"Connection failed for {measurement['sensor_id']} "
            f"(Is the server running at {API_URL}?)"
        )

    except requests.exceptions.Timeout:
        logger.error(f"Timeout for {measurement['sensor_id']}")
    except Exception as e:
        logger.error(f"Unexpected error for {measurement['sensor_id']}: {e}")


def main():
    """Main loop - continuously send measurements from all sensors."""
    logger.info(f"Starting sensor simulator...")
    logger.info(f"Sending data to: {API_URL}")
    logger.info(f"Simulating {len(SENSORS)} sensors")
    logger.info(f"Interval: {INTERVAL_SECONDS} seconds")
    logger.info("-" * 60)
    try:
        while True:
            for sensor_id in SENSORS:
                measurement = generate_measurement(sensor_id)
                send_measurement(measurement)
                time.sleep(INTERVAL_SECONDS)
    except KeyboardInterrupt:
        logger.error("\n\nStopping simulator...")
        logger.error("Goodbye!")


if __name__ == "__main__":
    main()
