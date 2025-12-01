from operations.aggregation_tasks import AggregationTaskManager
from utils.logger_config import setup_logging

logger = setup_logging("setup")

def main():
    """Set up all aggregation tasks."""
    logger.info("=" * 60)
    logger.info("Setting up InfluxDB aggregation tasks")
    logger.info("=" * 60)
    logger.info("")
    
    manager = AggregationTaskManager()
    
    try:
        # List existing tasks
        logger.info("Checking existing tasks...")
        existing_tasks = manager.list_tasks()
        logger.info("")
        
        # Set up aggregation tasks
        logger.info("Creating aggregation tasks...")
        success = manager.setup_all_tasks()
        
        if success:
            logger.info("")
            logger.info("=" * 60)
            logger.info("Setup complete!")
            logger.info("=" * 60)
            logger.info("")
            logger.info("Background tasks are now running:")
            logger.info("  • 1-minute aggregations: Runs every 1 minute")
            logger.info("  • 5-minute aggregations: Runs every 5 minutes")
            logger.info("")
            logger.info("Data will be stored in:")
            logger.info("  • water_quality (raw measurements)")
            logger.info("  • water_quality_1m (1-minute aggregations)")
            logger.info("  • water_quality_5m (5-minute aggregations)")
            logger.info("")
            logger.info("You can now start the API server and simulator.")
        else:
            logger.error("")
            logger.error("=" * 60)
            logger.error("Setup failed")
            logger.error("=" * 60)
            logger.error("")
            logger.error("Please check:")
            logger.error("  1. InfluxDB is running (docker-compose up -d)")
            logger.error("  2. Environment variables are set correctly")
            logger.error("  3. Check logs above for specific errors")
    
    finally:
        manager.close()


if __name__ == '__main__':
    main()

