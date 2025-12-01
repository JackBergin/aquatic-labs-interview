"""
API Server for Water Quality Monitoring System
Flask-based REST API that receives sensor measurements and stores them in InfluxDB.
"""

from flask import Flask, request, jsonify
from datetime import datetime
from storage.influx_client import InfluxDBClient
from utils.logger_config import setup_logging

logger = setup_logging("api")

app = Flask(__name__)

# Initialize InfluxDB client
influx_client = InfluxDBClient()


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return (
        jsonify(
            {"status": "healthy", "timestamp": datetime.utcnow().isoformat() + "Z"}
        ),
        200,
    )


@app.route("/measurements", methods=["POST"])
def create_measurement():
    """Receive and store sensor measurements."""
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["sensor_id", "timestamp", "temperature", "conductivity"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return (
                jsonify(
                    {"error": "Missing required fields", "missing": missing_fields}
                ),
                400,
            )

        # Validate data types
        if not isinstance(data["temperature"], (int, float)):
            return jsonify({"error": "temperature must be a number"}), 400

        if not isinstance(data["conductivity"], (int, float)):
            return jsonify({"error": "conductivity must be a number"}), 400

        # Store measurement in InfluxDB
        success = influx_client.write_measurement(
            sensor_id=data["sensor_id"],
            timestamp=data["timestamp"],
            temperature=data["temperature"],
            conductivity=data["conductivity"],
        )

        if success:
            return jsonify({"message": "Success", "sensor_id": data["sensor_id"]}), 201
        else:
            return jsonify({"error": "Failure"}), 500

    except Exception as e:
        logger.error(f"Error processing measurement: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route("/measurements/<sensor_id>", methods=["GET"])
def get_measurements(sensor_id):
    """Retrieve measurements for a specific sensor."""
    try:
        start_time = request.args.get("start")
        end_time = request.args.get("end")
        limit = int(request.args.get("limit", 100))

        measurements = influx_client.read_measurements(
            sensor_id=sensor_id, start_time=start_time, end_time=end_time, limit=limit
        )

        return (
            jsonify(
                {
                    "sensor_id": sensor_id,
                    "count": len(measurements),
                    "measurements": measurements,
                }
            ),
            200,
        )

    except ValueError:
        return jsonify({"error": "Invalid limit parameter"}), 400
    except Exception as e:
        logger.error(f"Error retrieving measurements: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route("/sensors", methods=["GET"])
def list_sensors():
    """List all sensors that have sent measurements."""
    try:
        sensors = influx_client.list_sensors()
        return jsonify({"count": len(sensors), "sensors": sensors}), 200
    except Exception as e:
        logger.error(f"Error listing sensors: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route("/measurements/<sensor_id>/aggregated", methods=["GET"])
def get_aggregated_measurements(sensor_id):
    """
    Retrieve aggregated measurements for a specific sensor.

    Automatically selects resolution based on time range:
    - 1-minute windows for the most recent hour
    - 5-minute windows for anything past that

    Query parameters:
    - start: Start time (ISO format or relative like "-1h", default: "-7d")
    - end: End time (ISO format, optional)
    - window: Override automatic window selection ("1m", "5m", "15m", "1h")
    """
    try:
        start_time = request.args.get("start", "-7d")
        end_time = request.args.get("end")
        window = request.args.get("window")

        # Auto-select window based on time range if not specified
        if not window:
            # Parse relative time to determine appropriate window
            if start_time.startswith("-"):
                # Extract the time value
                if "m" in start_time:  # minutes
                    minutes = int(start_time.replace("-", "").replace("m", ""))
                    window = "1m" if minutes <= 60 else "5m"
                elif "h" in start_time:  # hours
                    hours = int(start_time.replace("-", "").replace("h", ""))
                    window = "1m" if hours <= 1 else "5m"
                elif "d" in start_time:  # days
                    window = "5m"
                else:
                    window = "5m"
            else:
                # Default to 5m for absolute timestamps
                window = "5m"

        measurements = influx_client.read_aggregated_measurements(
            sensor_id=sensor_id, start_time=start_time, end_time=end_time, window=window
        )

        return (
            jsonify(
                {
                    "sensor_id": sensor_id,
                    "count": len(measurements),
                    "window": window,
                    "measurements": measurements,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error retrieving aggregated measurements: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


@app.route("/measurements/<sensor_id>/statistics", methods=["GET"])
def get_measurement_statistics(sensor_id):
    """
    Retrieve detailed statistics (mean, min, max, count) for sensor measurements.

    Automatically selects resolution based on time range:
    - 1-minute windows for the most recent hour
    - 5-minute windows for anything past that

    Query parameters:
    - start: Start time (ISO format or relative like "-1h", default: "-7d")
    - end: End time (ISO format, optional)
    - window: Override automatic window selection ("1m", "5m", "15m", "1h")
    """
    try:
        start_time = request.args.get("start", "-7d")
        end_time = request.args.get("end")
        window = request.args.get("window")

        # Auto-select window based on time range if not specified
        if not window:
            if start_time.startswith("-"):
                if "m" in start_time:
                    minutes = int(start_time.replace("-", "").replace("m", ""))
                    window = "1m" if minutes <= 60 else "5m"
                elif "h" in start_time:
                    hours = int(start_time.replace("-", "").replace("h", ""))
                    window = "1m" if hours <= 1 else "5m"
                elif "d" in start_time:
                    window = "5m"
                else:
                    window = "5m"
            else:
                window = "5m"

        statistics = influx_client.read_aggregated_statistics(
            sensor_id=sensor_id, start_time=start_time, end_time=end_time, window=window
        )

        return (
            jsonify(
                {
                    "sensor_id": sensor_id,
                    "count": len(statistics),
                    "window": window,
                    "statistics": statistics,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error retrieving statistics: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


if __name__ == "__main__":
    logger.info("Starting Water Quality Monitoring API...")
    logger.info("API will be available at: http://localhost:8081")
    app.run(host="0.0.0.0", port=8081, debug=True)
