import redis
import json
import logging
import threading
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)

class RedisHandler:
    """Handle Redis connections and pub/sub for the UI"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.host = host
        self.port = port
        self.db = db
        self.client = None
        self.pubsub = None
        self.running = False
        
    def connect(self):
        """Establish Redis connection"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                decode_responses=True
            )
            self.client.ping()
            logger.info(f"Connected to Redis at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            return False
    
    def start_listener(self, handlers: Dict[str, Callable[[Dict[str, Any]], None]]):
        """Start listening for Redis pub/sub messages"""
        if not self.connect():
            return
        
        try:
            self.pubsub = self.client.pubsub()
            # Subscribe to channels
            for channel in handlers.keys():
                self.pubsub.subscribe(channel)
                logger.info(f"Subscribed to channel: {channel}")
            
            self.running = True
            
            # Listen for messages
            for message in self.pubsub.listen():
                if not self.running:
                    break
                    
                if message['type'] == 'message':
                    channel = message['channel']
                    data = message['data']
                    
                    try:
                        # Parse JSON data
                        parsed_data = json.loads(data)
                        
                        # Call appropriate handler
                        if channel in handlers:
                            handlers[channel](parsed_data)
                            
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON from {channel}: {e}")
                    except Exception as e:
                        logger.error(f"Error handling message from {channel}: {e}")
                        
        except Exception as e:
            logger.error(f"Redis listener error: {e}")
        finally:
            self.stop_listener()
    
    def stop_listener(self):
        """Stop the Redis listener"""
        self.running = False
        if self.pubsub:
            self.pubsub.close()
        if self.client:
            self.client.close()
        logger.info("Redis listener stopped")
    
    def publish_command(self, channel: str, value: float, command_type: str = 'digital'):
        """Publish a command to Redis"""
        try:
            if not self.client:
                self.connect()
            
            command = {
                'command': 'set_output',
                'channel': channel,
                'value': value,
                'type': command_type
            }
            
            result = self.client.publish('commands', json.dumps(command))
            logger.info(f"Published command to {channel}: {value} (subscribers: {result})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish command: {e}")
            return False 