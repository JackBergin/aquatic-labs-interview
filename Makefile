.PHONY: help install setup-db setup-tasks start-api start-simulator run-all stop clean test health

# Default Python interpreter
PYTHON := python3
PIP := pip3

# Project paths
STORAGE_DIR := storage
API_MODULE := api.app
SIMULATOR_MODULE := simulation.sensor_simulator
AGGREGATION_MODULE := operations.aggregation_runner

# Colors for output
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Aquatic Labs Water Quality Monitoring System$(NC)"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick start:"
	@echo "  1. make install       # Install dependencies"
	@echo "  2. make setup-db      # Start InfluxDB"
	@echo "  3. make setup-tasks   # Setup aggregation tasks"
	@echo "  4. make run-all       # Start API + Simulator"

install: ## Install Python dependencies
	@echo "$(YELLOW)Installing dependencies...$(NC)"
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

setup-env: ## Create virtual environment
	@echo "$(YELLOW)Creating virtual environment...$(NC)"
	$(PYTHON) -m venv env
	@echo "$(GREEN)✓ Virtual environment created$(NC)"
	@echo "$(YELLOW)Activate with: source env/bin/activate$(NC)"

setup-db: ## Start InfluxDB using Docker Compose
	@echo "$(YELLOW)Starting InfluxDB...$(NC)"
	cd $(STORAGE_DIR) && docker-compose up -d
	@echo "$(YELLOW)Waiting for InfluxDB to be ready...$(NC)"
	@sleep 5
	@until curl -sf http://localhost:8086/health > /dev/null 2>&1; do \
		echo "$(YELLOW)Waiting for InfluxDB...$(NC)"; \
		sleep 2; \
	done
	@echo "$(GREEN)✓ InfluxDB is running$(NC)"
	@docker ps | grep influxdb

setup-tasks: ## Setup InfluxDB aggregation tasks
	@echo "$(YELLOW)Setting up aggregation tasks...$(NC)"
	$(PYTHON) -m $(AGGREGATION_MODULE)
	@echo "$(GREEN)✓ Aggregation tasks configured$(NC)"

start-api: ## Start the Flask API server
	@echo "$(YELLOW)Starting API server...$(NC)"
	$(PYTHON) -m $(API_MODULE)

start-simulator: ## Start the sensor simulator
	@echo "$(YELLOW)Starting sensor simulator...$(NC)"
	$(PYTHON) -m $(SIMULATOR_MODULE)

run-all: ## Run API and Simulator in background
	@echo "$(YELLOW)Starting all services...$(NC)"
	@echo "$(YELLOW)Starting API server in background...$(NC)"
	@$(PYTHON) -m $(API_MODULE) > logs/api.log 2>&1 & echo $$! > logs/.api.pid
	@sleep 2
	@echo "$(GREEN)✓ API server started (PID: $$(cat logs/.api.pid))$(NC)"
	@echo "$(YELLOW)Starting sensor simulator in background...$(NC)"
	@$(PYTHON) -m $(SIMULATOR_MODULE) > logs/simulator.log 2>&1 & echo $$! > logs/.simulator.pid
	@sleep 2
	@echo "$(GREEN)✓ Simulator started (PID: $$(cat logs/.simulator.pid))$(NC)"
	@echo ""
	@echo "$(GREEN)All services running!$(NC)"
	@echo "  API:       http://localhost:8081"
	@echo "  InfluxDB:  http://localhost:8086"
	@echo ""
	@echo "View logs:"
	@echo "  API:       tail -f logs/api.log"
	@echo "  Simulator: tail -f logs/simulator.log"
	@echo ""
	@echo "Stop with: make stop"

stop: ## Stop all running services
	@echo "$(YELLOW)Stopping services...$(NC)"
	@if [ -f logs/.api.pid ]; then \
		kill $$(cat logs/.api.pid) 2>/dev/null || true; \
		rm logs/.api.pid; \
		echo "$(GREEN)✓ API server stopped$(NC)"; \
	fi
	@if [ -f logs/.simulator.pid ]; then \
		kill $$(cat logs/.simulator.pid) 2>/dev/null || true; \
		rm logs/.simulator.pid; \
		echo "$(GREEN)✓ Simulator stopped$(NC)"; \
	fi
	@pkill -f "$(API_MODULE)" 2>/dev/null || true
	@pkill -f "$(SIMULATOR_MODULE)" 2>/dev/null || true
	@echo "$(GREEN)✓ All services stopped$(NC)"

stop-db: ## Stop InfluxDB
	@echo "$(YELLOW)Stopping InfluxDB...$(NC)"
	cd $(STORAGE_DIR) && docker-compose down
	@echo "$(GREEN)✓ InfluxDB stopped$(NC)"

clean: stop stop-db ## Stop all services and clean up
	@echo "$(YELLOW)Cleaning up...$(NC)"
	@rm -f logs/.api.pid logs/.simulator.pid
	@rm -rf logs/*.log
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

logs-api: ## Tail API logs
	@tail -f logs/api.log

logs-simulator: ## Tail simulator logs
	@tail -f logs/simulator.log

logs-influxdb: ## View InfluxDB logs
	@cd $(STORAGE_DIR) && docker-compose logs -f influxdb

health: ## Check health of all services
	@echo "$(YELLOW)Checking service health...$(NC)"
	@echo ""
	@echo "InfluxDB:"
	@if curl -sf http://localhost:8086/health > /dev/null 2>&1; then \
		echo "  $(GREEN)✓ Running$(NC)"; \
	else \
		echo "  $(RED)✗ Not running$(NC)"; \
	fi
	@echo ""
	@echo "API Server:"
	@if curl -sf http://localhost:8081/health > /dev/null 2>&1; then \
		echo "  $(GREEN)✓ Running$(NC)"; \
	else \
		echo "  $(RED)✗ Not running$(NC)"; \
	fi
	@echo ""
	@echo "Processes:"
	@if [ -f logs/.api.pid ]; then \
		echo "  API PID: $$(cat logs/.api.pid)"; \
	fi
	@if [ -f logs/.simulator.pid ]; then \
		echo "  Simulator PID: $$(cat logs/.simulator.pid)"; \
	fi

test-api: ## Test API endpoints
	@echo "$(YELLOW)Testing API endpoints...$(NC)"
	@echo ""
	@echo "Health check:"
	@curl -s http://localhost:8081/health | python3 -m json.tool
	@echo ""
	@echo "List sensors:"
	@curl -s http://localhost:8081/sensors | python3 -m json.tool
	@echo ""
	@echo "$(GREEN)✓ API is responding$(NC)"

test-submit: ## Submit a test measurement
	@echo "$(YELLOW)Submitting test measurement...$(NC)"
	@curl -X POST http://localhost:8081/measurements \
		-H "Content-Type: application/json" \
		-d '{"sensor_id":"test_sensor","timestamp":"'$$(date -u +%Y-%m-%dT%H:%M:%SZ)'","temperature":25.5,"conductivity":1500}' \
		| python3 -m json.tool
	@echo ""
	@echo "$(GREEN)✓ Test measurement submitted$(NC)"

setup-logs: ## Create logs directory
	@mkdir -p logs
	@echo "$(GREEN)✓ Logs directory created$(NC)"

setup: setup-db setup-tasks setup-logs ## Complete setup (DB + Tasks + Logs)
	@echo ""
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)✓ Setup complete!$(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@echo "Next steps:"
	@echo "  1. make run-all     # Start API and Simulator"
	@echo "  2. make health      # Check service status"
	@echo "  3. make test-api    # Test API endpoints"

dev-api: ## Run API in development mode (foreground)
	@echo "$(YELLOW)Starting API in development mode...$(NC)"
	$(PYTHON) -m $(API_MODULE)

dev-simulator: ## Run simulator in development mode (foreground)
	@echo "$(YELLOW)Starting simulator in development mode...$(NC)"
	$(PYTHON) -m $(SIMULATOR_MODULE)

list-tasks: ## List InfluxDB aggregation tasks
	@echo "$(YELLOW)Listing aggregation tasks...$(NC)"
	$(PYTHON) -m operations.aggregation_tasks list

delete-tasks: ## Delete all aggregation tasks
	@echo "$(YELLOW)Deleting aggregation tasks...$(NC)"
	$(PYTHON) -m operations.aggregation_tasks delete

status: health ## Alias for health check

restart: stop run-all ## Restart all services

restart-api: ## Restart only the API server
	@if [ -f logs/.api.pid ]; then \
		kill $$(cat logs/.api.pid) 2>/dev/null || true; \
		rm logs/.api.pid; \
	fi
	@$(MAKE) --no-print-directory start-api

restart-simulator: ## Restart only the simulator
	@if [ -f logs/.simulator.pid ]; then \
		kill $$(cat logs/.simulator.pid) 2>/dev/null || true; \
		rm logs/.simulator.pid; \
	fi
	@$(MAKE) --no-print-directory start-simulator

influxdb-ui: ## Open InfluxDB UI in browser
	@echo "$(YELLOW)Opening InfluxDB UI...$(NC)"
	@echo "URL: http://localhost:8086"
	@echo "Username: admin"
	@echo "Password: adminpassword"
	@open http://localhost:8086 2>/dev/null || xdg-open http://localhost:8086 2>/dev/null || echo "Open http://localhost:8086 in your browser"

query-raw: ## Query raw measurements (example)
	@echo "$(YELLOW)Querying raw measurements for sensor_001 (last hour)...$(NC)"
	@curl -s "http://localhost:8081/measurements/sensor_001?start=-1h&limit=10" | python3 -m json.tool

query-aggregated: ## Query aggregated measurements (example)
	@echo "$(YELLOW)Querying aggregated measurements for sensor_001 (last hour)...$(NC)"
	@curl -s "http://localhost:8081/measurements/sensor_001/aggregated?start=-1h" | python3 -m json.tool

query-stats: ## Query statistics (example)
	@echo "$(YELLOW)Querying statistics for sensor_001 (last 2 hours)...$(NC)"
	@curl -s "http://localhost:8081/measurements/sensor_001/statistics?start=-2h" | python3 -m json.tool

# Docker shortcuts
docker-ps: ## Show running containers
	@docker ps

docker-logs: ## Show InfluxDB container logs
	@cd $(STORAGE_DIR) && docker-compose logs

# Development helpers
format: ## Format Python code with black (if installed)
	@if command -v black > /dev/null; then \
		echo "$(YELLOW)Formatting Python code...$(NC)"; \
		black . --exclude env/; \
		echo "$(GREEN)✓ Code formatted$(NC)"; \
	else \
		echo "$(RED)black not installed. Install with: pip install black$(NC)"; \
	fi

lint: ## Run linting (if installed)
	@if command -v flake8 > /dev/null; then \
		echo "$(YELLOW)Running linter...$(NC)"; \
		flake8 . --exclude env/ --max-line-length=120; \
		echo "$(GREEN)✓ Linting complete$(NC)"; \
	else \
		echo "$(RED)flake8 not installed. Install with: pip install flake8$(NC)"; \
	fi

