# Simulation Module

This module simulates water quality sensors that continuously generate and send measurements to the API.

## Overview

The sensor simulator generates realistic temperature and conductivity measurements for 3 sensors, mimicking a real-world IoT deployment. Data is sent to the API server via HTTP POST requests.

## Files

- `sensor_simulator.py` - Main simulator script
- `__init__.py` - Python package initialization

## Sensor Configuration

**Number of Sensors:** 3 (sensor_001, sensor_002, sensor_003)

**Measurement Rate:** 2 measurements per second per sensor (total: 6 measurements/second)

**Measurement Interval:** 0.5 seconds between measurements

**Parameters:**
- **Temperature:** 18-28°C with random variation
- **Conductivity:** 1200-1800 µS/cm with random variation

## Running the Simulator

### Using Makefile (Recommended)

Run as part of the full system:
```bash
make run-all
```

Run in development mode (foreground with logging):
```bash
make dev-simulator
```

View simulator logs:
```bash
make logs-simulator
```

### Manual Execution

```bash
# Ensure virtual environment is activated
source env/bin/activate

# Run the simulator
python3 -m simulation.sensor_simulator
```

### Expected Output

```
Starting sensor simulator...
Sending data for 3 sensors every 0.5 seconds to http://localhost:8081/measurements
Press Ctrl+C to stop

[2024-12-01 10:30:00] sensor_001: temp=25.3°C, cond=1542 µS/cm → Success
[2024-12-01 10:30:00] sensor_002: temp=23.7°C, cond=1456 µS/cm → Success
[2024-12-01 10:30:00] sensor_003: temp=26.1°C, cond=1623 µS/cm → Success
...
```

## Configuration

The simulator uses these default settings:

```python
API_URL = "http://localhost:8081/measurements"
SENSOR_IDS = ["sensor_001", "sensor_002", "sensor_003"]
SLEEP_INTERVAL = 0.5  # seconds between measurements
TEMP_MIN = 18.0       # minimum temperature (°C)
TEMP_MAX = 28.0       # maximum temperature (°C)
COND_MIN = 1200       # minimum conductivity (µS/cm)
COND_MAX = 1800       # maximum conductivity (µS/cm)
```

To modify these, edit `sensor_simulator.py` directly.

## API Endpoint

The simulator sends POST requests to:
```
POST http://localhost:8081/measurements
```

**Request Body:**
```json
{
  "sensor_id": "sensor_001",
  "timestamp": "2024-12-01T10:30:00+00:00",
  "temperature": 25.3,
  "conductivity": 1542
}
```

## Error Handling

The simulator includes robust error handling:
- Retries failed requests with exponential backoff
- Logs detailed error messages including HTTP status codes
- Continues running even if the API is temporarily unavailable
- Graceful shutdown on Ctrl+C

## Development

### Running in Debug Mode

Use VSCode debug configuration "Debug Sensor Simulator" from `.vscode/launch.json`:
1. Open `simulation/sensor_simulator.py`
2. Press F5 or use Run > Start Debugging
3. Set breakpoints as needed

### Modifying Sensor Behavior

To change sensor characteristics, edit the measurement generation logic in `sensor_simulator.py`:

```python
def generate_measurement(sensor_id):
    return {
        "sensor_id": sensor_id,
        "timestamp": datetime.now(UTC).isoformat(),
        "temperature": round(random.uniform(TEMP_MIN, TEMP_MAX), 2),
        "conductivity": round(random.uniform(COND_MIN, COND_MAX), 2)
    }
```

## Logs

Logs are written to:
- Console (stdout)
- `logs/simulator.log` (when run via Makefile)

Log format:
```
[timestamp] sensor_id: temp=XX.X°C, cond=XXXX µS/cm → Status
```

## Stopping the Simulator

**If running in foreground:**
Press `Ctrl+C`

**If running via Makefile:**
```bash
make stop
```

This will gracefully stop the simulator and clean up the PID file.

