"""
API Server for Water Quality Monitoring System
Flask-based REST API that receives sensor measurements and stores them in InfluxDB.
"""
from flask import Flask, request, jsonify
from datetime import datetime
from utils.logger_config import setup_logging
from storage.influx_client import InfluxDBClient

logger = setup_logging("api")

app = Flask(__name__)

# Initialize InfluxDB client
influx_client = InfluxDBClient()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

@app.route('/measurements', methods=['POST'])
def create_measurement():
    """Receive and store sensor measurements."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['sensor_id', 'timestamp', 'temperature', 'conductivity']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return jsonify({
                'error': 'Missing required fields',
                'missing': missing_fields
            }), 400
        
        # Validate data types
        if not isinstance(data['temperature'], (int, float)):
            return jsonify({'error': 'temperature must be a number'}), 400
        
        if not isinstance(data['conductivity'], (int, float)):
            return jsonify({'error': 'conductivity must be a number'}), 400
        
        # Store measurement in InfluxDB
        success = influx_client.write_measurement(
            sensor_id=data['sensor_id'],
            timestamp=data['timestamp'],
            temperature=data['temperature'],
            conductivity=data['conductivity']
        )
        
        if success:
            return jsonify({
                'message': 'Success',
                'sensor_id': data['sensor_id']
            }), 201
        else:
            return jsonify({
                'error': 'Failure'
            }), 500
            
    except Exception as e:
        logger.error(f"Error processing measurement: {e}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/measurements/<sensor_id>', methods=['GET'])
def get_measurements(sensor_id):
    """Retrieve measurements for a specific sensor."""
    try:
        start_time = request.args.get('start')
        end_time = request.args.get('end')
        limit = int(request.args.get('limit', 100))
        
        measurements = influx_client.read_measurements(
            sensor_id=sensor_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        
        return jsonify({
            'sensor_id': sensor_id,
            'count': len(measurements),
            'measurements': measurements
        }), 200
        
    except ValueError:
        return jsonify({'error': 'Invalid limit parameter'}), 400
    except Exception as e:
        logger.error(f"Error retrieving measurements: {e}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

@app.route('/sensors', methods=['GET'])
def list_sensors():
    """List all sensors that have sent measurements."""
    try:
        sensors = influx_client.list_sensors()
        return jsonify({
            'count': len(sensors),
            'sensors': sensors
        }), 200
    except Exception as e:
        logger.error(f"Error listing sensors: {e}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    logger.info("Starting Water Quality Monitoring API...")
    logger.info("API will be available at: http://localhost:8081")
    app.run(host='0.0.0.0', port=8081, debug=True)

