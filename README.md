# Water Quality Monitoring System

This contains the code I did for the full stack IoT swe position at aquatic labs. The project is composed of a sensor simulator, api, and db that simulates a sensor's data collection, storage, and retrieval capabilities.


## Overview

This system simulates sensors that measure temperature and conductivity, stores the data in a time-series database (InfluxDB), and provides a REST API for data access.

## System Architecture

Simulation ──HTTP──▶   API   ──Flux──▶  InfluxDB     

### Components

1. Simulation (/simulation) - Simulates sensors
2. API (/api) - Flask REST API for receiving and serving measurements
3. Storage (/storage) - InfluxDB client for time-series data management
4. Database - InfluxDB 2.7 running in Docker

## Project Structure

```
aquatic-labs-interview/
├── simulation/              # Sensor simulator
│   ├── sensor_simulator.py  # Main simulator script
│   └─- __init__.py          # Init file
├── api/                    # REST API server
│   ├── app.py              # Flask application
│   └── README.md          # API documentation
├── storage/                # Database layer
│   ├── influx_client.py    # InfluxDB client wrapper
│   ├── docker-compose.yml  # InfluxDB container setup
│   └── README.md          # Storage documentation
├── requirements.txt        # All project dependencies
├── .env.local             # All project .env values
├── .gitignore             # Git ignore rules
└── README.md              # This file
```

## Quick Start

### 1. Install Dependencies

Create and activate a virtual environment:

```bash
python3 -m venv env
source env/bin/activate  
```

Install Python packages:

```bash
pip install -r requirements.txt
```

### 2. Start InfluxDB

Launch InfluxDB using Docker Compose:

```bash
cd storage && docker-compose up -d
```

Verify InfluxDB is running:

```bash
docker ps
```

### 3. Start the API Server

```bash
python -m api.app
```

The API will be available at `http://localhost:8081`

### 4. Run the Sensor Simulator

In a new terminal (with the virtual environment activated):

```bash
python3 -m simulation.sensor_simulator
```

You should see measurements being sent

## API Endpoints

### Submit Measurement
```bash
POST /measurements
Content-Type: application/json

{
  "sensor_id": "sensor_001",
  "timestamp": "2024-12-01T10:30:00Z",
  "temperature": 25.3,
  "conductivity": 1542
}
```

### Get Measurements
```bash
GET /measurements/sensor_001?limit=10
```

### List All Sensors
```bash
GET /sensors
```

### Health Check
```bash
GET /health
```


## Testing the API
Refer to [API README](api/README.md)


### Accessing InfluxDB UI

The InfluxDB web interface is available at `http://localhost:8086`

Login credentials:
- **Username:** `admin`
- **Password:** `adminpassword`

### InfluxDB Schema

- Measurement: water_quality
- Tags: sensor_id
- Fields: temperature (float), conductivity (float)
- Timestamp: ISO 8601 format with nanosecond precision

## Author

Jack Bergin
