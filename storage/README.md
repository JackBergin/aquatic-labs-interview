# Storage Module

This module provides the InfluxDB client for storing and retrieving sensor measurements.

## Overview

The storage module handles all interactions with InfluxDB time-series database:
- Writing raw sensor measurements with proper timestamps
- Querying raw historical data with flexible time ranges
- Reading pre-computed aggregated statistics (mean, min, max)
- Listing all active sensors

## Files

- `influx_client.py` - Main InfluxDB client wrapper with read/write methods
- `docker-compose.yml` - Docker Compose configuration for InfluxDB
- `__init__.py` - Python package initialization

## Data Model

The system uses a three-measurement schema for efficient storage and querying:

### 1. water_quality (Raw Measurements)
Stores all raw sensor data as it arrives.

- **Measurement Name:** `water_quality`
- **Tags:** `sensor_id`
- **Fields:** `temperature` (float), `conductivity` (float)
- **Retention:** All data retained
- **Write Rate:** ~6 points/second (3 sensors × 2 measurements/second)

### 2. water_quality_1m (1-Minute Aggregations)
Pre-computed statistics for recent data (last hour).

- **Measurement Name:** `water_quality_1m`
- **Tags:** `sensor_id`, `stat_type` (mean|min|max)
- **Fields:** `temperature` (float), `conductivity` (float)
- **Computed By:** Background tasks running every 1 minute
- **Use Case:** Queries ≤ 1 hour use this for faster responses

### 3. water_quality_5m (5-Minute Aggregations)
Pre-computed statistics for older data (beyond 1 hour).

- **Measurement Name:** `water_quality_5m`
- **Tags:** `sensor_id`, `stat_type` (mean|min|max)
- **Fields:** `temperature` (float), `conductivity` (float)
- **Computed By:** Background tasks running every 5 minutes
- **Use Case:** Queries > 1 hour use this for efficient historical queries

## InfluxDB Setup

The InfluxDB instance should be running before using this module. Use Docker Compose:

```bash
cd storage
docker-compose up -d
```

Or use the Makefile:
```bash
make setup-db
```

This will:
1. Start InfluxDB 2.7 on port 8086
2. Create organization: `aquatic-labs`
3. Create bucket: `water-quality`
4. Set up admin credentials (admin/adminpassword)

## Accessing InfluxDB UI

The InfluxDB web interface is available at `http://localhost:8086`

**Credentials:**
- Username: `admin`
- Password: `adminpassword`
- Organization: `aquatic-labs`
- Bucket: `water-quality`

You can use the UI to:
- Browse raw and aggregated data
- Write and test Flux queries
- Monitor background tasks
- View system metrics
