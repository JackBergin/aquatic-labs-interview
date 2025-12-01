import os
from influxdb_client import InfluxDBClient as InfluxClient
from utils.logger_config import setup_logging
from influxdb_client.domain.task_create_request import TaskCreateRequest

logger = setup_logging("aggregation_tasks")


class AggregationTaskManager:
    """Manages InfluxDB tasks for automatic data aggregation and downsampling."""

    def __init__(self):
        self.url = os.getenv("INFLUXDB_URL", "http://localhost:8086")
        self.token = os.getenv("INFLUXDB_TOKEN", "my-super-secret-auth-token")
        self.org = os.getenv("INFLUXDB_ORG", "aquatic-labs")
        self.bucket = os.getenv("INFLUXDB_BUCKET", "water-quality")

        self.client = InfluxClient(url=self.url, token=self.token, org=self.org)
        self.tasks_api = self.client.tasks_api()

        logger.info("Aggregation Task Manager initialized")

    def _create_aggregation_task(self, task_name, window, stat_fn, stat_type):
        """
        Helper to create a single aggregation task.

        Args:
            task_name: Name of the task
            window: Time window (e.g., "1m", "5m")
            stat_fn: Aggregation function (mean, min, max, count)
            stat_type: Type label (mean, min, max, count)
        """
        existing_tasks = self.tasks_api.find_tasks(name=task_name)
        if existing_tasks:
            logger.info(f"Task '{task_name}' already exists")
            return existing_tasks[0]

        # Determine time range based on window
        if window == "1m":
            start_time = "-2m"
            stop_time = "-1m"
            every = "1m"
            offset = "10s"
        else:  # 5m
            start_time = "-70m"
            stop_time = "-65m"
            every = "5m"
            offset = "30s"

        flux_script = f"""
option task = {{
  name: "{task_name}",
  every: {every},
  offset: {offset}
}}

from(bucket: "{self.bucket}")
  |> range(start: {start_time}, stop: {stop_time})
  |> filter(fn: (r) => r["_measurement"] == "water_quality")
  |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "conductivity")
  |> aggregateWindow(every: {window}, fn: {stat_fn}, createEmpty: false)
  |> set(key: "stat_type", value: "{stat_type}")
  |> set(key: "_measurement", value: "water_quality_{window}")
  |> to(bucket: "{self.bucket}")
"""

        try:
            task_request = TaskCreateRequest(
                org=self.org, flux=flux_script, status="active"
            )

            task = self.tasks_api.create_task(task_create_request=task_request)
            logger.info(f"Created task: {task_name}")
            return task
        except Exception as e:
            logger.error(f"Error creating task {task_name}: {e}")
            return None

    def create_one_minute_aggregation_task(self):
        """Create all 1-minute aggregation tasks (mean, min, max)."""
        tasks = []
        tasks.append(
            self._create_aggregation_task("aggregate_1m_mean", "1m", "mean", "mean")
        )
        tasks.append(
            self._create_aggregation_task("aggregate_1m_min", "1m", "min", "min")
        )
        tasks.append(
            self._create_aggregation_task("aggregate_1m_max", "1m", "max", "max")
        )
        return all(t is not None for t in tasks)

    def create_five_minute_aggregation_task(self):
        """Create all 5-minute aggregation tasks (mean, min, max)."""
        tasks = []
        tasks.append(
            self._create_aggregation_task("aggregate_5m_mean", "5m", "mean", "mean")
        )
        tasks.append(
            self._create_aggregation_task("aggregate_5m_min", "5m", "min", "min")
        )
        tasks.append(
            self._create_aggregation_task("aggregate_5m_max", "5m", "max", "max")
        )
        return all(t is not None for t in tasks)

    def setup_all_tasks(self):
        """Set up all aggregation tasks (6 total: 3 for 1m, 3 for 5m)."""
        logger.info("Setting up aggregation tasks...")
        logger.info("Creating 1-minute aggregation tasks (mean, min, max)...")

        task_1m = self.create_one_minute_aggregation_task()

        logger.info("Creating 5-minute aggregation tasks (mean, min, max)...")
        task_5m = self.create_five_minute_aggregation_task()

        if task_1m and task_5m:
            logger.info("All aggregation tasks configured successfully (6 tasks)")
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
        # Delete 1-minute tasks
        self.delete_task("aggregate_1m_mean")
        self.delete_task("aggregate_1m_min")
        self.delete_task("aggregate_1m_max")
        self.delete_task("aggregate_1m_count")
        # Delete 5-minute tasks
        self.delete_task("aggregate_5m_mean")
        self.delete_task("aggregate_5m_min")
        self.delete_task("aggregate_5m_max")
        self.delete_task("aggregate_5m_count")
        # Delete old task names if they exist
        self.delete_task("aggregate_1m_windows")
        self.delete_task("aggregate_5m_windows")
        logger.info("Cleanup complete")

    def close(self):
        """Close the InfluxDB client connection."""
        if self.client:
            self.client.close()


if __name__ == "__main__":
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
