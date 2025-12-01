import os
from influxdb_client import InfluxDBClient as InfluxClient
from utils.logger_config import setup_logging
from influxdb_client.domain.task_create_request import TaskCreateRequest

logger = setup_logging("aggregation_tasks")

class AggregationTaskManager:
    """Manages InfluxDB tasks for automatic data aggregation and downsampling."""
    
    def __init__(self):
        self.url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
        self.token = os.getenv('INFLUXDB_TOKEN', 'my-super-secret-auth-token')
        self.org = os.getenv('INFLUXDB_ORG', 'aquatic-labs')
        self.bucket = os.getenv('INFLUXDB_BUCKET', 'water-quality')
        
        self.client = InfluxClient(url=self.url, token=self.token, org=self.org)
        self.tasks_api = self.client.tasks_api()
        
        logger.info("Aggregation Task Manager initialized")
    
    def create_one_minute_aggregation_task(self):
        """
        Create a task that aggregates raw data into 1-minute windows.
        Runs every minute to aggregate the previous minute's data.
        """
        task_name = "aggregate_1m_windows"
        
        # Check if task already exists
        existing_tasks = self.tasks_api.find_tasks(name=task_name)
        if existing_tasks:
            logger.info(f"Task '{task_name}' already exists")
            return existing_tasks[0]
        
        # Flux script for 1-minute aggregation
        flux_script = f'''
option task = {{
  name: "{task_name}",
  every: 1m,
  offset: 10s
}}

data = from(bucket: "{self.bucket}")
  |> range(start: -2m, stop: -1m)
  |> filter(fn: (r) => r["_measurement"] == "water_quality")
  |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "conductivity")

data
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
  |> set(key: "stat_type", value: "mean")
  |> set(key: "_measurement", value: "water_quality_1m")
  |> to(bucket: "{self.bucket}")

data
  |> aggregateWindow(every: 1m, fn: min, createEmpty: false)
  |> set(key: "stat_type", value: "min")
  |> set(key: "_measurement", value: "water_quality_1m")
  |> to(bucket: "{self.bucket}")

data
  |> aggregateWindow(every: 1m, fn: max, createEmpty: false)
  |> set(key: "stat_type", value: "max")
  |> set(key: "_measurement", value: "water_quality_1m")
  |> to(bucket: "{self.bucket}")

data
  |> aggregateWindow(every: 1m, fn: count, createEmpty: false)
  |> set(key: "stat_type", value: "count")
  |> set(key: "_measurement", value: "water_quality_1m")
  |> to(bucket: "{self.bucket}")
'''
        
        try:            
            task_request = TaskCreateRequest(
                org=self.org,
                flux=flux_script,
                status="active"
            )
            
            task = self.tasks_api.create_task(task_create_request=task_request)
            logger.info(f"Created task: {task_name}")
            return task
        except Exception as e:
            logger.error(f"Error creating 1m aggregation task: {e}")
            return None
    
    def create_five_minute_aggregation_task(self):
        """
        Create a task that downsamples 1-minute data to 5-minute windows.
        Runs every 5 minutes for data older than 1 hour.
        """
        task_name = "aggregate_5m_windows"
        
        # Check if task already exists
        existing_tasks = self.tasks_api.find_tasks(name=task_name)
        if existing_tasks:
            logger.info(f"Task '{task_name}' already exists")
            return existing_tasks[0]
        
        # Flux script for 5-minute aggregation from raw data older than 1 hour
        flux_script = f'''
option task = {{
  name: "{task_name}",
  every: 5m,
  offset: 30s
}}

data = from(bucket: "{self.bucket}")
  |> range(start: -70m, stop: -65m)
  |> filter(fn: (r) => r["_measurement"] == "water_quality")
  |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "conductivity")

data
  |> aggregateWindow(every: 5m, fn: mean, createEmpty: false)
  |> set(key: "stat_type", value: "mean")
  |> set(key: "_measurement", value: "water_quality_5m")
  |> to(bucket: "{self.bucket}")

data
  |> aggregateWindow(every: 5m, fn: min, createEmpty: false)
  |> set(key: "stat_type", value: "min")
  |> set(key: "_measurement", value: "water_quality_5m")
  |> to(bucket: "{self.bucket}")

data
  |> aggregateWindow(every: 5m, fn: max, createEmpty: false)
  |> set(key: "stat_type", value: "max")
  |> set(key: "_measurement", value: "water_quality_5m")
  |> to(bucket: "{self.bucket}")

data
  |> aggregateWindow(every: 5m, fn: count, createEmpty: false)
  |> set(key: "stat_type", value: "count")
  |> set(key: "_measurement", value: "water_quality_5m")
  |> to(bucket: "{self.bucket}")
'''
        
        try:            
            task_request = TaskCreateRequest(
                org=self.org,
                flux=flux_script,
                status="active"
            )
            
            task = self.tasks_api.create_task(task_create_request=task_request)
            logger.info(f"Created task: {task_name}")
            return task
        except Exception as e:
            logger.error(f"Error creating 5m aggregation task: {e}")
            return None
    
    def setup_all_tasks(self):
        """Set up all aggregation tasks."""
        logger.info("Setting up aggregation tasks...")
        
        task_1m = self.create_one_minute_aggregation_task()
        task_5m = self.create_five_minute_aggregation_task()
        
        if task_1m and task_5m:
            logger.info("All aggregation tasks configured successfully")
            return True
        else:
            logger.error("Failed to configure some aggregation tasks")
            return False
    
    def list_tasks(self):
        """List all existing aggregation tasks."""
        try:
            tasks = self.tasks_api.find_tasks()
            logger.info(f"Found {len(tasks)} tasks:")
            for task in tasks:
                status = "active" if task.status == "active" else "inactive"
                logger.info(f"  - {task.name}: {status}")
            return tasks
        except Exception as e:
            logger.error(f"Error listing tasks: {e}")
            return []
    
    def delete_task(self, task_name):
        """Delete a specific task by name."""
        try:
            tasks = self.tasks_api.find_tasks(name=task_name)
            if tasks:
                for task in tasks:
                    self.tasks_api.delete_task(task.id)
                    logger.info(f"Deleted task: {task_name}")
                return True
            else:
                logger.warning(f"Task not found: {task_name}")
                return False
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
            return False
    
    def delete_all_aggregation_tasks(self):
        """Delete all aggregation tasks (useful for cleanup/reset)."""
        logger.info("Deleting all aggregation tasks...")
        self.delete_task("aggregate_1m_windows")
        self.delete_task("aggregate_5m_windows")
        logger.info("Cleanup complete")
    
    def close(self):
        """Close the InfluxDB client connection."""
        if self.client:
            self.client.close()


if __name__ == '__main__':
    """Setup aggregation tasks when run directly."""
    import sys
    
    manager = AggregationTaskManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "setup":
            manager.setup_all_tasks()
        elif command == "list":
            manager.list_tasks()
        elif command == "delete":
            manager.delete_all_aggregation_tasks()
        else:
            print("Usage: python aggregation_tasks.py [setup|list|delete]")
    else:
        # Default: setup tasks
        manager.setup_all_tasks()
    
    manager.close()

