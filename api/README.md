# API Module

This module contains the Flask-based REST API that receives sensor measurements and stores them in InfluxDB.

## Overview

The API provides endpoints for:
- Receiving sensor measurements via POST requests
- Retrieving historical measurements for specific sensors
- Listing all active sensors
- Health checking

## Files

- app.py - Main Flask application with all API endpoints
- __init__.py - Python package initialization

## API Endpoints

### POST /measurements
Submit a new sensor measurement.

#### Request Body:
```json
{
  "sensor_id": "sensor_001",
  "timestamp": "2024-12-01T10:30:00Z",
  "temperature": 25.3,
  "conductivity": 1542
}
```

#### Response (201 Created):
```json
{
  "message": "Success",
  "sensor_id": "sensor_001"
}
```

### GET /measurements/<sensor_id>
Retrieve measurements for a specific sensor.

Query Parameters:
- start - Start time (ISO format, optional)
- end   - End time (ISO format, optional)
- limit - Maximum records to return (default: 100)

Example:
```
GET /measurements/sensor_001?limit=50
```

Response (200 OK):
```json
{
  "sensor_id": "sensor_001",
  "count": 50,
  "measurements": [
    {
      "timestamp": "2024-12-01T10:30:00Z",
      "sensor_id": "sensor_001",
      "temperature": 25.3,
      "conductivity": 1542
    }
  ]
}
```

### GET /sensors
List all sensors that have sent measurements.

Response (200 OK):
```json
{
  "count": 3,
  "sensors": ["sensor_001", "sensor_002", "sensor_003"]
}
```

### GET /health
Health check endpoint.

Response (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-12-01T10:30:00Z"
}
```

## Running the API


```bash
python -m api.app
```

The API will start on http://localhost:8081 with debug mode enabled.


## Testing the API

### Using curl

Submit a measurement:
```bash
curl -X POST http://localhost:5000/measurements \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "sensor_001",
    "timestamp": "2024-12-01T10:30:00Z",
    "temperature": 25.3,
    "conductivity": 1542
  }'
```

Get measurements:
```bash
curl http://localhost:5000/measurements/sensor_001?limit=10
```

List sensors:
```bash
curl http://localhost:5000/sensors
```

Health check:
```bash
curl http://localhost:5000/health
```