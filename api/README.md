# API Module

This module contains the Flask-based REST API that receives sensor measurements and stores them in InfluxDB.

## Overview

The API provides endpoints for:
- Receiving sensor measurements via POST requests
- Retrieving raw historical measurements for specific sensors
- Retrieving aggregated measurements with automatic downsampling
- Retrieving detailed statistics (mean, min, max, count)
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
Retrieve raw measurements for a specific sensor.

Query Parameters:
- start - Start time (ISO format or relative like "-1h", optional)
- end   - End time (ISO format, optional)
- limit - Maximum records to return (default: 100)

Example:
```
GET /measurements/sensor_001?start=-1h&limit=50
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

### GET /measurements/<sensor_id>/aggregated
Retrieve pre-computed aggregated measurements with automatic resolution selection.

Note: This endpoint reads from pre-computed aggregations, not raw data.

Automatic Resolution Selection:
- Queries ≤ 1 hour: Uses `water_quality_1m` (1-minute windows)
- Queries > 1 hour: Uses `water_quality_5m` (5-minute windows)

Query Parameters:
- start - Start time (relative like "-1h" or ISO format, default: "-7d")
- end   - End time (ISO format, optional)
- window - Override automatic window selection ("1m", "5m", "15m", "1h", optional)

Example:
```
GET /measurements/sensor_001/aggregated?start=-1h
```

Response (200 OK):
```json
{
  "sensor_id": "sensor_001",
  "count": 60,
  "window": "1m",
  "measurements": [
    {
      "timestamp": "2024-12-01T10:30:00Z",
      "sensor_id": "sensor_001",
      "temperature": 25.3,
      "conductivity": 1542,
      "window": "1m"
    }
  ]
}
```

### GET /measurements/<sensor_id>/statistics
Retrieve detailed pre-computed statistics (mean, min, max) with automatic resolution selection.

This endpoint reads from pre-computed aggregations stored by background tasks.

Query Parameters:
- start - Start time (relative like "-1h" or ISO format, default: "-7d")
- end   - End time (ISO format, optional)
- window - Override automatic window selection ("1m", "5m", "15m", "1h", optional)

Example:
```
GET /measurements/sensor_001/statistics?start=-2h
```

Response (200 OK):
```json
{
  "sensor_id": "sensor_001",
  "count": 24,
  "window": "5m",
  "statistics": [
    {
      "timestamp": "2024-12-01T10:30:00Z",
      "sensor_id": "sensor_001",
      "window": "5m",
      "temperature": {
        "mean": 25.3,
        "min": 24.5,
        "max": 26.1
      },
      "conductivity": {
        "mean": 1542,
        "min": 1520,
        "max": 1565
      }
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

## Setup

### Prerequisites

1. InfluxDB must be running:
```bash
cd storage && docker-compose up -d
```

2. Setup aggregation tasks (required for aggregated/statistics endpoints):
```bash
python3 -m operations.aggregation_runner
```

This creates 6 background tasks that pre-compute aggregations (mean, min, max for 1m and 5m windows).

### Running the API

```bash
python -m api.app
```

The API will start on http://localhost:8081 with debug mode enabled.


## Testing the API

### Using curl

Submit a measurement:
```bash
curl -X POST http://localhost:8081/measurements \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "sensor_001",
    "timestamp": "2024-12-01T10:30:00Z",
    "temperature": 25.3,
    "conductivity": 1542
  }'
```

Get raw measurements:
```bash
curl http://localhost:8081/measurements/sensor_001?start=-1h&limit=10
```

Get aggregated measurements (auto-selects 1m window for last hour):
```bash
curl http://localhost:8081/measurements/sensor_001/aggregated?start=-1h
```

Get aggregated measurements with 5m window:
```bash
curl http://localhost:8081/measurements/sensor_001/aggregated?start=-7d&window=5m
```

Get statistics with automatic window selection:
```bash
curl http://localhost:8081/measurements/sensor_001/statistics?start=-2h
```

List sensors:
```bash
curl http://localhost:8081/sensors
```

Health check:
```bash
curl http://localhost:8081/health
```