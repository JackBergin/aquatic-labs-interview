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
│  │• mean,min,max, │      │• mean,min,max, │       │
│  │  count         │      │  count         │       │
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

- [API Reference](api/README.md) - Complete API endpoint documentation
- [Makefile Guide](MAKEFILE_GUIDE.md) - How to use the Makefile
- [Storage Layer](storage/README.md) - InfluxDB client documentation  
- [Architecture & Design Decisions](ARCHITECTURE.md) - System design rationale

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
# Complete setup
make setup        # Sets up InfluxDB + aggregation tasks

# Start all services
make run-all      # Starts API + Simulator in background

# Check status
make health       # Verify all services are running

# View logs
make logs-api     # Tail API logs
make logs-simulator  # Tail simulator logs

# Stop everything
make stop         # Stop all services
```

**Quick Start One-Liner:**
```bash
make install && make setup && make run-all
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

This creates two InfluxDB tasks:
- **1-minute aggregation**: Runs every minute for recent data
- **5-minute aggregation**: Runs every 5 minutes for data older than 1 hour

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

```bash
make help              # Show all available commands
make install           # Install Python dependencies
make setup             # Complete setup (DB + Tasks)
make run-all           # Start API + Simulator
make stop              # Stop all services
make health            # Check service status
make test-api          # Test API endpoints
make query-aggregated  # Query aggregated data
make clean             # Clean up everything
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

**Get Statistics** (mean, min, max, count from pre-computed data)
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
Refer to [API README](api/README.md)


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
- Computed every minute for recent data
- Contains: mean, min, max, count

**3. water_quality_5m** (5-Minute Aggregations)
- Tags: sensor_id, stat_type
- Fields: temperature, conductivity
- Computed every 5 minutes for data older than 1 hour
- Contains: mean, min, max, count

## Author

Jack Bergin
