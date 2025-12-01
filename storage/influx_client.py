import os
from influxdb_client import InfluxDBClient as InfluxClient
from influxdb_client.client.write_api import SYNCHRONOUS

from utils.logger_config import setup_logging

logger = setup_logging("influx_db_client")

class InfluxDBClient:
    """Client for interacting with InfluxDB."""
    
    def __init__(self):
        self.url = os.getenv('INFLUXDB_URL', 'http://localhost:8086')
        self.token = os.getenv('INFLUXDB_TOKEN', 'my-super-secret-auth-token')
        self.org = os.getenv('INFLUXDB_ORG', 'aquatic-labs')
        self.bucket = os.getenv('INFLUXDB_BUCKET', 'water-quality')
        
        # Initialize client
        self.client = InfluxClient(url=self.url, token=self.token, org=self.org)
        self.write_api = self.client.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.client.query_api()
        
        logger.info(f"InfluxDB Client initialized:")
        logger.info(f"  URL: {self.url}")
        logger.info(f"  Org: {self.org}")
        logger.info(f"  Bucket: {self.bucket}")
    
    def close(self):
        """Close the InfluxDB client connection."""
        if self.client:
            self.client.close()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

