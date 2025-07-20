import os
from dotenv import load_dotenv

class Config:
    """Configuration class for DAQ system"""
    
    def __init__(self):
        # Load environment variables
        self.load_config()
    
    def load_config(self):
        """Load configuration from environment variables"""
        # Redis configuration
        self.redis_host = os.getenv('REDIS_HOST', 'localhost')
        self.redis_port = int(os.getenv('REDIS_PORT', '6379'))
        self.redis_db = int(os.getenv('REDIS_DB', '0'))
        self.redis_channel = os.getenv('REDIS_CHANNEL', 'sensors')
        
        # InfluxDB configuration
        self.influxdb_host = os.getenv('INFLUXDB_HOST', 'localhost')
        self.influxdb_port = int(os.getenv('INFLUXDB_PORT', '8086'))
        self.influxdb_org = os.getenv('INFLUXDB_ORG', 'DAQ')
        self.influxdb_bucket = os.getenv('INFLUXDB_BUCKET', 'logger')
        self.influxdb_token = os.getenv('INFLUXDB_TOKEN', '')
        
        # Logger configuration
        self.influxdb_samples_trigger = int(os.getenv('INFLUXDB_SAMPLES_TRIGGER', '1000'))
        self.influxdb_time_trigger = int(os.getenv('INFLUXDB_TIME_TRIGGER', '10')) 