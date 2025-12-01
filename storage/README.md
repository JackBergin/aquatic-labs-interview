# Storage Module

This module provides the InfluxDB client for storing and retrieving sensor measurements.

## Overview

The storage module handles all interactions with InfluxDB time-series database:
- Writing sensor measurements with proper timestamps
- Querying historical data with flexible time ranges

## Data Model

### Measurement Point

Data is stored in InfluxDB with this structure:

- **Measurement Name:** `water_quality`
- **Tags:** `sensor_id`
- **Fields:** `temperature`, `conductivity`

## InfluxDB Setup

The InfluxDB instance should be running before using this module. Use Docker Compose:

```bash
docker-compose up -d
```

This will:
1. Start InfluxDB 2.7 on port 8086
2. Create organization: `aquatic-labs`
3. Create bucket: `water-quality`
