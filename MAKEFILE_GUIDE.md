# Makefile Usage Guide

This project includes a comprehensive Makefile for managing the entire system lifecycle.

## Quick Start

```bash
# Complete setup and run
make install      # Install dependencies
make setup        # Setup database and aggregation tasks
make run-all      # Start all services in background
make health       # Verify everything is running
```

## Available Commands

### Setup & Installation

```bash
make install          # Install Python dependencies
make setup-env        # Create virtual environment
make setup-db         # Start InfluxDB with Docker
make setup-tasks      # Configure aggregation tasks
make setup            # Complete setup (DB + Tasks + Logs)
```

### Running Services

```bash
make run-all          # Start API + Simulator in background
make start-api        # Start API server (foreground)
make start-simulator  # Start simulator (foreground)
make dev-api          # Run API in development mode
make dev-simulator    # Run simulator in development mode
```

### Monitoring & Logs

```bash
make health           # Check health of all services
make status           # Alias for health
make logs-api         # Tail API server logs
make logs-simulator   # Tail simulator logs
make logs-influxdb    # View InfluxDB logs
```

### Testing

```bash
make test-api         # Test API endpoints
make test-submit      # Submit a test measurement
make query-raw        # Query raw measurements
make query-aggregated # Query aggregated data
make query-stats      # Query statistics
```

### Management

```bash
make stop             # Stop API + Simulator
make stop-db          # Stop InfluxDB
make restart          # Restart all services
make restart-api      # Restart only API
make restart-simulator # Restart only simulator
make clean            # Stop everything and clean up
```

### InfluxDB Tasks

```bash
make list-tasks       # List aggregation tasks
make delete-tasks     # Delete all aggregation tasks
```

### Docker

```bash
make docker-ps        # Show running containers
make docker-logs      # Show InfluxDB logs
```

### Development

```bash
make format           # Format code with black
make lint             # Run linting with flake8
```

### Help

```bash
make help             # Show all available commands
```

## Common Workflows

### Initial Setup
```bash
make install
make setup
make run-all
make health
```

### Daily Development
```bash
# Terminal 1: API in foreground
make dev-api

# Terminal 2: Simulator in foreground  
make dev-simulator
```

### Background Mode
```bash
make run-all
make logs-api        # In separate terminal
make logs-simulator  # In another terminal
make stop           # When done
```

### Testing After Changes
```bash
make restart
make test-api
make query-aggregated
```

### Cleanup & Restart
```bash
make clean
make setup
make run-all
```

## Service Endpoints

- **API Server**: http://localhost:8081
- **InfluxDB UI**: http://localhost:8086
  - Username: `admin`
  - Password: `adminpassword`

## Log Files

Logs are stored in the `logs/` directory:
- `logs/api.log` - API server logs
- `logs/simulator.log` - Simulator logs

## Process Management

When using `make run-all`, process IDs are stored in:
- `.api.pid` - API server PID
- `.simulator.pid` - Simulator PID

These files are automatically created and cleaned up by the Makefile.

## Troubleshooting

### Services won't start
```bash
make clean
make setup
make run-all
```

### Check what's running
```bash
make health
make docker-ps
```

### View logs for errors
```bash
make logs-api
make logs-simulator
make logs-influxdb
```

### Reset everything
```bash
make clean
make stop-db
# Wait a moment, then
make setup
make run-all
```

## Tips

1. **Use `make help`** to see all available commands
2. **Background mode** (`make run-all`) is great for demos
3. **Foreground mode** (`make dev-api`) is better for development
4. **Always check health** after starting services
5. **View logs** when debugging issues

