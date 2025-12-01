# Aquatic Labs Take Home Project

This contains the code I did for the full stack IoT swe position at aquatic labs. The project is composed of a sensor simulator, api, and db that simulates a sensor's data collection, storage, and retrieval capabilities.


## Overview

This system simulates sensors that measure temperature and conductivity, stores the data in a time-series database (InfluxDB), runs a job to precompute the data aggregates and provides a REST API for data access.

## System Architecture

```
┌─────────────────┐
│   Simulator     │  Generates sensor data (2 measurements/sec × 3 sensors)
│  (3 sensors)    │
└────────┬────────┘
         │ HTTP POST
         ▼
┌─────────────────┐
│   Flask API     │  Receives and validates measurements
│                 │
└────────┬────────┘
         │ Write
         ▼
┌───────────────────────────────────────────--──────┐
│             InfluxDB                              │
│                                                   │
│  ┌───────────────────────────────────────────┐    │
│  │ sensor_data   (Raw Data)                  │    │
│  │ • All raw measurements                    │    │
│  │ • No aggregation                          │    │
│  └───────────────────────────────────────────┘    │
│         │                          │              │
│         │                          │              │
│  ┌──────▼───────-───┐       ┌──────▼────────────┐ │
│  │  Background Task │       │  Background Task  │ │
│  │  (Every 1 minute)│       │  (Every 5 minutes)│ │
│  └──────┬─────-─────┘       └──────┬─────────--─┘ │
│         │                          │              │
│         ▼                          ▼              │
│  ┌────────────────┐      ┌────────────────┐       │
│  │sensor_data_1m  │      │sensor_data_5m  │       │
│  │(1-min windows) │      │(5-min windows) │       │
│  │• Last 1 hour   │      │• Older than 1hr│       │
│  │• mean,min,max  │      │• mean,min,max  │       │
│  └────────────────┘      └────────────────┘       │
│         ▲                         ▲               │
│         └─────────┬───────────────┘               │
│                   │ Read (Query)                  │
└───────────────────┼───────────────────────────────┘
                    │
             ┌──────▼──────┐
             │  Flask API  │  Queries pre-computed aggregations
             │             │
             └─────────────┘
```

### Components

1. Simulation (/simulation) - Simulates sensors
2. API (/api) - Flask REST API for receiving and serving measurements
3. Storage (/storage) - InfluxDB client for time-series data management
4. Database - InfluxDB 2.7 running in Docker

## Documentation

### Module Documentation
- **[API Reference](api/README.md)** - REST API endpoints, request/response formats, testing examples
- **[Storage Layer](storage/README.md)** - InfluxDB client, data model, database schema
- **[Simulation](simulation/README.md)** - Sensor simulator configuration and usage
- **[Operations](operations/README.md)** - Aggregation tasks, background jobs, task management

### Quick Reference
- Run `make help` to see all available Makefile commands
- See examples below for common API usage patterns

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

### Using Makefile (Recommended)

The easiest way to run the entire system:

```bash
# 1. Install dependencies (if not already done)
make install

# 2. Complete setup (starts InfluxDB + creates aggregation tasks)
make setup

# 3. Start all services (API + Simulator in background)
make run-all

# 4. Check everything is running
make health

# 5. Test the API
make test-api
```

**Quick Start One-Liner:**
```bash
make install && make setup && make run-all && sleep 3 && make health
```

**View real-time logs:**
```bash
make logs-api        # Tail API logs
make logs-simulator  # Tail simulator logs
```

**Stop everything:**
```bash
make stop           # Stop API + Simulator
make stop-db        # Stop InfluxDB
```

### Manual Setup

<details>
<summary>Click to expand manual setup instructions</summary>

#### 1. Install Dependencies

Create and activate a virtual environment:

```bash
python3 -m venv env
source env/bin/activate  
```

Install Python packages:

```bash
pip install -r requirements.txt
```

#### 2. Start InfluxDB

Launch InfluxDB using Docker Compose:

```bash
cd storage && docker-compose up -d
```

Verify InfluxDB is running:

```bash
docker ps
```

#### 3. Setup Aggregation Tasks

This sets up background tasks that automatically compute and store aggregations:

```bash
python3 -m operations.aggregation_runner
```

This creates 6 InfluxDB tasks that run automatically:
- **1-minute aggregations** (3 tasks): mean, min, max - runs every minute
- **5-minute aggregations** (3 tasks): mean, min, max - runs every 5 minutes

These tasks continuously compute statistics as new data arrives.

#### 4. Start the API Server

```bash
python -m api.app
```

The API will be available at `http://localhost:8081`

#### 5. Run the Sensor Simulator

In a new terminal (with the virtual environment activated):

```bash
python3 -m simulation.sensor_simulator
```

You should see measurements being sent

</details>

## Makefile Commands

Run `make help` to see all available commands. Key commands:

```bash
# Setup & Installation
make install           # Install Python dependencies
make setup             # Complete setup (InfluxDB + aggregation tasks + logs)
make setup-db          # Start InfluxDB only
make setup-tasks       # Setup aggregation tasks only

# Running Services
make run-all           # Start API + Simulator in background
make dev-api           # Run API in foreground (for development)
make dev-simulator     # Run simulator in foreground

# Monitoring
make health            # Check all service health
make logs-api          # Tail API logs
make logs-simulator    # Tail simulator logs
make logs-influxdb     # View InfluxDB logs

# Testing
make test-api          # Test basic API endpoints
make query-raw         # Query raw measurements
make query-aggregated  # Query aggregated data (mean values)
make query-stats       # Query statistics (mean, min, max)

# Maintenance
make stop              # Stop API + Simulator
make stop-db           # Stop InfluxDB
make clean             # Stop everything + cleanup
make restart           # Restart all services
```

## API Endpoints

### Raw Data

**Submit Measurement**
```bash
POST /measurements
```

**Get Raw Measurements**
```bash
GET /measurements/sensor_001?start=-1h&limit=10
```

### Pre-Computed Aggregations

**Get Aggregated Measurements** (reads from pre-computed data)
```bash
GET /measurements/sensor_001/aggregated?start=-1h
```

**Get Statistics** (mean, min, max from pre-computed data)
```bash
GET /measurements/sensor_001/statistics?start=-2h
```

The API automatically selects the appropriate pre-computed measurement:
- Queries ≤ 1 hour: Uses `water_quality_1m` (1-minute windows)
- Queries > 1 hour: Uses `water_quality_5m` (5-minute windows)

### Utility Endpoints

**List All Sensors**
```bash
GET /sensors
```

**Health Check**
```bash
GET /health
```


## Testing the API

### Quick Tests Using Makefile

```bash
# Test basic endpoints
make test-api

# Query raw measurements (last hour, 10 records)
make query-raw

# Query aggregated data (mean values, last hour)  
make query-aggregated

# Query statistics (mean, min, max, last 2 hours)
make query-stats
```

### Manual Testing with curl

**Submit a test measurement:**
```bash
curl -X POST http://localhost:8081/measurements \
  -H "Content-Type: application/json" \
  -d '{
    "sensor_id": "test_sensor",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
    "temperature": 25.5,
    "conductivity": 1500
  }'
```

**Get raw measurements:**
```bash
curl "http://localhost:8081/measurements/sensor_001?start=-1h&limit=10" | python3 -m json.tool
```

**Get aggregated measurements (mean values):**
```bash
curl "http://localhost:8081/measurements/sensor_001/aggregated?start=-1h" | python3 -m json.tool
```

**Get detailed statistics (mean, min, max):**
```bash
curl "http://localhost:8081/measurements/sensor_001/statistics?start=-2h" | python3 -m json.tool
```

**List all sensors:**
```bash
curl "http://localhost:8081/sensors" | python3 -m json.tool
```

For more examples and detailed documentation, see the **[API README](api/README.md)**.


### Accessing InfluxDB UI

The InfluxDB web interface is available at `http://localhost:8086`

Login credentials:
- **Username:** `admin`
- **Password:** `adminpassword`

### InfluxDB Schema

The system stores data in three measurements:

**1. water_quality** (Raw Data)
- Tags: sensor_id
- Fields: temperature, conductivity
- Stores all raw sensor measurements

**2. water_quality_1m** (1-Minute Aggregations)
- Tags: sensor_id, stat_type
- Fields: temperature, conductivity
- Computed every minute for recent data (last hour)
- Contains: mean, min, max

**3. water_quality_5m** (5-Minute Aggregations)
- Tags: sensor_id, stat_type
- Fields: temperature, conductivity
- Computed every 5 minutes for older data (beyond 1 hour)
- Contains: mean, min, max

## Author

Jack Bergin
