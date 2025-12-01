import os
from influxdb_client import InfluxDBClient as InfluxClient, Point
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
    
    def write_measurement(self, sensor_id, timestamp, temperature, conductivity):
        """Write a sensor measurement to InfluxDB."""
        try:
            # Create a point with the measurement data
            point = Point("water_quality") \
                .tag("sensor_id", sensor_id) \
                .field("temperature", float(temperature)) \
                .field("conductivity", float(conductivity)) \
                .time(timestamp)
            
            # Write to InfluxDB
            self.write_api.write(bucket=self.bucket, record=point)
            return True
            
        except Exception as e:
            logger.error(f"Error writing to InfluxDB: {e}")
            return False
    
    def read_measurements(self, sensor_id, start_time=None, end_time=None, limit=100):
        """
        Read measurements from InfluxDB for a specific sensor.
        Args:
            sensor_id (str): Unique identifier for the sensor
            start_time (str): Start time in ISO format or relative time (e.g., "-1h")
            end_time (str): End time in ISO format (optional)
            limit (int): A limit for the number of returned measurements
        Returns:

        """
        try:
            # Build Flux query
            time_range = start_time if start_time else "-7d"
            
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {time_range})
                |> filter(fn: (r) => r["_measurement"] == "water_quality")
                |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
                |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "conductivity")
                |> pivot(rowKey:["_time"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: true)
                |> limit(n: {limit})
            '''
            
            # Execute query
            tables = self.query_api.query(query, org=self.org)
            
            # Parse results
            measurements = []
            for table in tables:
                for record in table.records:
                    measurements.append({
                        'timestamp': record.get_time().isoformat(),
                        'sensor_id': record.values.get('sensor_id'),
                        'temperature': record.values.get('temperature'),
                        'conductivity': record.values.get('conductivity')
                    })
            
            return measurements
            
        except Exception as e:
            logger.error(f"Error reading from InfluxDB: {e}")
            return []
    
    def list_sensors(self):
        """ Get a list of all sensors that have sent measurements."""
        try:
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: -30d)
                |> filter(fn: (r) => r["_measurement"] == "water_quality")
                |> keep(columns: ["sensor_id"])
                |> distinct(column: "sensor_id")
            '''
            
            tables = self.query_api.query(query, org=self.org)
            
            sensors = []
            for table in tables:
                for record in table.records:
                    sensor_id = record.values.get('sensor_id')
                    if sensor_id and sensor_id not in sensors:
                        sensors.append(sensor_id)
            
            return sorted(sensors)
            
        except Exception as e:
            logger.error(f"Error listing sensors from InfluxDB: {e}")
            return []
    
    def read_aggregated_measurements(self, sensor_id, start_time=None, end_time=None, window="1m"):
        """
        Read pre-computed aggregated measurements from InfluxDB.
        
        Reads from:
        - water_quality_1m for 1-minute aggregations
        - water_quality_5m for 5-minute aggregations
        
        Args:
            sensor_id (str): Unique identifier for the sensor
            start_time (str): Start time in ISO format or relative time (e.g., "-1h")
            end_time (str): End time in ISO format (optional)
            window (str): Aggregation window ("1m" or "5m")
        
        Returns:
            list: List of aggregated measurement dictionaries (mean values)
        """
        try:
            time_range = start_time if start_time else "-7d"
            
            # Select the appropriate pre-aggregated measurement
            measurement_name = f"water_quality_{window}"
            
            # Query pre-computed aggregations (mean values)
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {time_range}'''
            
            if end_time:
                query += f', stop: {end_time}'
            
            query += f''')
                |> filter(fn: (r) => r["_measurement"] == "{measurement_name}")
                |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
                |> filter(fn: (r) => r["stat_type"] == "mean")
                |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "conductivity")
                |> pivot(rowKey:["_time", "sensor_id"], columnKey: ["_field"], valueColumn: "_value")
                |> sort(columns: ["_time"], desc: true)
            '''
            
            tables = self.query_api.query(query, org=self.org)
            
            measurements = []
            for table in tables:
                for record in table.records:
                    measurements.append({
                        'timestamp': record.get_time().isoformat(),
                        'sensor_id': record.values.get('sensor_id'),
                        'temperature': record.values.get('temperature'),
                        'conductivity': record.values.get('conductivity'),
                        'window': window
                    })
            
            return measurements
            
        except Exception as e:
            logger.error(f"Error reading aggregated data from InfluxDB: {e}")
            return []
    
    def read_aggregated_statistics(self, sensor_id, start_time=None, end_time=None, window="1m"):
        """
        Read detailed pre-computed statistics (mean, min, max, count) from InfluxDB.
        
        Reads from pre-aggregated measurements:
        - water_quality_1m for 1-minute windows
        - water_quality_5m for 5-minute windows
        
        Args:
            sensor_id (str): Unique identifier for the sensor
            start_time (str): Start time in ISO format or relative time
            end_time (str): End time in ISO format (optional)
            window (str): Aggregation window ("1m" or "5m")
        
        Returns:
            list: List of statistical aggregations per time window
        """
        try:
            time_range = start_time if start_time else "-7d"
            measurement_name = f"water_quality_{window}"
            
            # Query all statistics from pre-computed aggregations
            query = f'''
            from(bucket: "{self.bucket}")
                |> range(start: {time_range}'''
            
            if end_time:
                query += f', stop: {end_time}'
                
            query += f''')
                |> filter(fn: (r) => r["_measurement"] == "{measurement_name}")
                |> filter(fn: (r) => r["sensor_id"] == "{sensor_id}")
                |> filter(fn: (r) => r["_field"] == "temperature" or r["_field"] == "conductivity")
                |> filter(fn: (r) => r["stat_type"] == "mean" or r["stat_type"] == "min" or r["stat_type"] == "max" or r["stat_type"] == "count")
                |> sort(columns: ["_time"], desc: true)
            '''
            
            tables = self.query_api.query(query, org=self.org)
            
            # Parse and organize results by timestamp
            stats_by_time = {}
            
            for table in tables:
                for record in table.records:
                    timestamp = record.get_time().isoformat()
                    sensor_id_val = record.values.get('sensor_id')
                    field = record.values.get('_field')
                    stat_type = record.values.get('stat_type')
                    value = record.values.get('_value')
                    
                    # Create key for this time window
                    key = f"{timestamp}_{sensor_id_val}"
                    
                    if key not in stats_by_time:
                        stats_by_time[key] = {
                            'timestamp': timestamp,
                            'sensor_id': sensor_id_val,
                            'window': window,
                            'temperature': {},
                            'conductivity': {}
                        }
                    
                    # Add statistic
                    if field and stat_type:
                        if field == 'temperature':
                            stats_by_time[key]['temperature'][stat_type] = value
                        elif field == 'conductivity':
                            stats_by_time[key]['conductivity'][stat_type] = value
            
            # Convert to list and sort by timestamp
            result = sorted(stats_by_time.values(), 
                          key=lambda x: x['timestamp'], 
                          reverse=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error reading aggregated statistics from InfluxDB: {e}")
            return []
    
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