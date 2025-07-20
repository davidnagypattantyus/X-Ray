#docker compose up --build -d logger
import asyncio
from redis.asyncio import Redis
import json
import os
import sys
from datetime import datetime
from typing import Dict, List
from dateutil import parser
from influxdb_client.client.influxdb_client_async import InfluxDBClientAsync
from influxdb_client import Point
from dotenv import load_dotenv
import pathlib
import signal
import time
from daq_core import Config

# Load environment variables from config.env in root directory
env_path = pathlib.Path(__file__).parent.parent / 'config.env'
load_dotenv(dotenv_path=env_path)

class AsyncDataLogger:
    def __init__(self):
        # Load configuration
        self.config = Config()
        
        # Configuration
        self.redis_channel = self.config.redis_channel
        self.samples_trigger = self.config.influxdb_samples_trigger
        self.time_trigger = self.config.influxdb_time_trigger
        
        # Enhanced status tracking
        self.messages_processed = 0
        self.messages_dropped = 0
        self.points_processed = 0
        self.points_dropped = 0
        self.points_written = 0
        self.last_write_time = time.time()
        self.write_errors = 0
        self.total_messages = 0
        self.last_timestamp = None
        self.max_gap = 0.0
        self.total_points_logged = 0
        
        # Shutdown flag
        self.should_stop = asyncio.Event()
        
        # Buffers with larger sizes
        self.fresh_buffer = []     # Newest points
        self.backlog_buffer = []   # Older points
        self.fresh_limit = 2000    # Points to keep in fresh buffer
        self.backlog_limit = 1000000  # 1 million point backlog
        self.last_push_time = time.time()

    def format_uptime(self, seconds: float) -> str:
        """Format uptime in HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    async def connect(self):
        """Initialize connections to Redis and InfluxDB"""
        # Redis connection
        try:
            self.redis = Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                decode_responses=True
            )
            await self.redis.ping()
            print(f"✓ Connected to Redis")
        except Exception as e:
            print(f"✕ Redis connection failed: {e}")
            raise

        # InfluxDB connection
        try:
            self.influx_client = InfluxDBClientAsync(
                url=f"http://{self.config.influxdb_host}:{self.config.influxdb_port}",
                token=self.config.influxdb_token,
                org=self.config.influxdb_org,
                bucket=self.config.influxdb_bucket,
                verify_ssl=False
            )
            
            self.write_api = self.influx_client.write_api()
            
            if await self.influx_client.ping():
                print(f"✓ Connected to InfluxDB")
            else:
                raise ConnectionError("InfluxDB ping failed")
                
        except Exception as e:
            print(f"✕ InfluxDB connection failed: {e}")
            raise

    def create_points(self, message: Dict) -> List[Point]:
        """Convert a message to InfluxDB points"""
        points = []
        timestamp = message['timestamp']
        
        for channel, channel_data in message['samples'].items():
            try:
                metadata = channel_data.get('metadata', {})
                raw_value = channel_data.get('value')
                value_type = metadata.get('value_type', 'FLOAT')
                device_type = metadata.get('type', 'unknown')
                
                # Convert all values to float
                if value_type == 'DIGITAL':
                    value = 1.0 if bool(raw_value) else 0.0
                elif value_type == 'INTEGER16':
                    value = float(raw_value) / 32768.0
                else:
                    value = float(raw_value)
                
                point = Point('sensor_data')\
                    .tag("Device", device_type)\
                    .tag("Channel", channel)\
                    .tag("IO_Type", metadata.get('io_type', 'unknown'))\
                    .tag("Data_Type", metadata.get('type', 'unknown'))\
                    .field("value", value)\
                    .time(timestamp)
                    
                points.append(point)
                
            except Exception as e:
                self.points_dropped += 1
                continue
            
        return points

    async def push_to_influx(self, force=False):
        """Push buffered points to InfluxDB with priority for fresh data"""
        current_time = time.time()
        time_since_push = current_time - self.last_push_time
        
        should_push = (
            len(self.fresh_buffer) >= self.fresh_limit or
            time_since_push >= self.time_trigger or
            force
        )
        
        if should_push:
            try:
                # Always try to write fresh data first
                if self.fresh_buffer:
                    await self.write_api.write(
                        bucket=self.config.influxdb_bucket,
                        record=self.fresh_buffer
                    )
                    self.points_written += len(self.fresh_buffer)
                    self.fresh_buffer = []
                
                # Then write some backlog if we have capacity
                if self.backlog_buffer:
                    backlog_chunk = self.backlog_buffer[:5000]  # Write 5000 backlog points
                    await self.write_api.write(
                        bucket=self.config.influxdb_bucket,
                        record=backlog_chunk
                    )
                    self.points_written += len(backlog_chunk)
                    self.backlog_buffer = self.backlog_buffer[5000:]
                
            except Exception as e:
                # On error, move fresh data to backlog
                if len(self.backlog_buffer) < self.backlog_limit:
                    self.backlog_buffer.extend(self.fresh_buffer)
                else:
                    self.points_dropped += len(self.fresh_buffer)
                self.fresh_buffer = []
                self.write_errors += 1
                print(f"✕ Write error: Moving {len(self.fresh_buffer)} points to backlog")
                raise
            finally:
                self.last_push_time = current_time

    async def process_message(self, channel: str, message: str):
        """Process a single message"""
        try:
            data = json.loads(message)
            if 'command' in data or 'samples' not in data:
                return
                
            points = self.create_points(data)
            
            # Add to fresh buffer, overflow to backlog
            space_in_fresh = self.fresh_limit - len(self.fresh_buffer)
            if space_in_fresh > 0:
                self.fresh_buffer.extend(points[:space_in_fresh])
                overflow = points[space_in_fresh:]
                if overflow and len(self.backlog_buffer) < self.backlog_limit:
                    self.backlog_buffer.extend(overflow)
                else:
                    self.points_dropped += len(overflow)
            else:
                if len(self.backlog_buffer) < self.backlog_limit:
                    self.backlog_buffer.extend(points)
                else:
                    self.points_dropped += len(points)
            
            await self.push_to_influx()
            
            self.messages_processed += 1
            self.total_messages += 1
            
        except Exception as e:
            self.messages_dropped += 1
            print(f"✕ Error: {e}")
            raise

    async def run(self):
        """Main async run loop"""
        start_timestamp = time.time()
        print("\nStarting logger...")
        
        while not self.should_stop.is_set():
            try:
                await self.connect()
                
                pubsub = self.redis.pubsub()
                await pubsub.subscribe(self.redis_channel)
                
                last_status_time = time.time()
                
                while not self.should_stop.is_set():
                    message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=0.1)
                    if message:
                        await self.process_message(message['channel'], message['data'])
                    
                    # Status update every 30 seconds
                    now = time.time()
                    if now - last_status_time >= 30:
                        uptime = self.format_uptime(now - start_timestamp)
                        print(f"\nLogger Stats:")
                        print(f"Uptime: {uptime}")
                        print(f"Fresh Buffer: {len(self.fresh_buffer):,} / {self.fresh_limit:,}")
                        print(f"Backlog: {len(self.backlog_buffer):,} / {self.backlog_limit:,}")
                        print(f"Points Written: {self.points_written:,}")
                        print(f"Points Dropped: {self.points_dropped:,}")
                        last_status_time = now
                        
            except Exception as e:
                print(f"✕ Error: {e}")
                await asyncio.sleep(5)

    async def shutdown(self):
        """Clean shutdown of the logger"""
        print("\nShutting down...")
        self.should_stop.set()
        
        # Final flush of any remaining points
        if self.fresh_buffer or self.backlog_buffer:
            try:
                await self.push_to_influx(force=True)
            except Exception as e:
                print(f"✕ Error in final write: {e}")
        
        # Close connections
        if hasattr(self, 'redis'):
            await self.redis.aclose()
        
        if hasattr(self, 'influx_client'):
            await self.influx_client.close()

def handle_signals():
    """Setup signal handlers"""
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(logger.shutdown()))

if __name__ == "__main__":
    logger = AsyncDataLogger()
    handle_signals()
    asyncio.run(logger.run()) 