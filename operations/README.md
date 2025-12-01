# Operations Module

This module manages InfluxDB background tasks for automatic data aggregation and downsampling.

## Overview

The operations module sets up and manages background tasks that continuously compute and store statistical aggregations (mean, min, max) at multiple time resolutions (1-minute and 5-minute windows). This pre-computation approach ensures fast query responses regardless of time range.

## Files

- `aggregation_tasks.py` - Core task management (create, delete, list tasks)
- `aggregation_runner.py` - CLI script to setup all aggregation tasks
- `__init__.py` - Python package initialization

## Architecture

### Pre-Computed Aggregation Strategy

Instead of computing statistics on-demand (which would be slow for large time ranges), the system uses InfluxDB's built-in task scheduler to pre-compute and store aggregations:

1. **Raw data** arrives at the API and is written to `water_quality` measurement
2. **Background tasks** run automatically every 1 or 5 minutes
3. **Aggregated data** is computed and written to `water_quality_1m` or `water_quality_5m`
4. **API queries** read from pre-computed aggregations for fast responses

### Task Schedule

**6 Background Tasks:**

| Task Name | Window | Statistic | Runs Every | Processes Data From |
|-----------|--------|-----------|------------|---------------------|
| aggregate_1m_mean | 1m | mean | 1 minute | Last 2 minutes |
| aggregate_1m_min | 1m | min | 1 minute | Last 2 minutes |
| aggregate_1m_max | 1m | max | 1 minute | Last 2 minutes |
| aggregate_5m_mean | 5m | mean | 5 minutes | Last 10 minutes |
| aggregate_5m_min | 5m | min | 5 minutes | Last 10 minutes |
| aggregate_5m_max | 5m | max | 5 minutes | Last 10 minutes |

## Setup

### Automated Setup (Recommended)

Use the Makefile:
```bash
make setup-tasks
```

This runs the aggregation runner and creates all 6 tasks automatically.

### Manual Setup

```bash
# Ensure virtual environment is activated
source env/bin/activate

# Ensure InfluxDB is running
make setup-db

# Run the aggregation setup script
python3 -m operations.aggregation_runner
```

## Task Management

### List All Tasks

```bash
python3 -m operations.aggregation_tasks list
```

Or via Makefile:
```bash
make list-tasks
```

### Delete All Tasks

```bash
python3 -m operations.aggregation_tasks delete
```

Or via Makefile:
```bash
make delete-tasks
```

### Recreate Tasks

If you need to modify or recreate tasks:
```bash
make delete-tasks
make setup-tasks
```

## How It Works

### 1-Minute Aggregation Example (Mean)

The Flux script that runs every minute:

```flux
option task = {
  name: "aggregate_1m_mean",
  every: 1m,
  offset: "10s"
}

from(bucket: "water-quality")
  |> range(start: -2m, stop: -1m)
  |> filter(fn: (r) => r["_measurement"] == "water_quality")
  |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "conductivity")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> set(key: "stat_type", value: "mean")
  |> set(key: "_measurement", value: "water_quality_1m")
  |> to(bucket: "water-quality")
```

**What this does:**
1. Runs every 1 minute (with 10s offset to avoid contention)
2. Looks at data from 2 minutes ago to 1 minute ago
3. Filters for raw `water_quality` measurements
4. Computes mean for temperature and conductivity
5. Tags result with `stat_type: "mean"`
6. Writes to `water_quality_1m` measurement

### 5-Minute Aggregation

Similar logic but:
- Runs every 5 minutes
- Processes last 10 minutes of data
- Writes to `water_quality_5m` measurement

## Monitoring Tasks

### Via InfluxDB UI

1. Open http://localhost:8086
2. Login (admin/adminpassword)
3. Navigate to **Tasks** (left sidebar)
4. View task runs, logs, and status

### Via API

Check task execution in logs:
```bash
make logs-influxdb
```

### Verify Aggregations

Test that aggregations are being created:

```bash
# Wait 2-3 minutes after setup
sleep 180

# Query aggregated data
make query-aggregated

# Query statistics
make query-stats
```

### Recreating Tasks

If tasks are in a bad state:
```bash
make delete-tasks
make setup-tasks
```


## Performance Considerations

- **Task Offset:** 10-second offset prevents all tasks from running simultaneously
- **Data Window:** Tasks process a 2-minute window (for 1m) to handle late-arriving data
- **Separate Pipelines:** Each statistic (mean, min, max) runs independently for reliability
- **Resource Usage:** Tasks are lightweight and run efficiently even with high data volumes

