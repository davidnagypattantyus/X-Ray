#docker compose up --build -d UI
from nicegui import ui, app
import os
import threading
import logging
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any
from redis_client import RedisHandler
from components import IOTable

# Load environment variables from config.env in root directory
env_path = Path(__file__).parent.parent / 'config.env'
load_dotenv(dotenv_path=env_path)

# Configuration
REFRESH_RATE = 0.15  # seconds

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set up static file serving
static_dir = Path(__file__).parent / 'static'
app.add_static_files('/static', static_dir)

class UI:
    def __init__(self):
        self.redis = RedisHandler(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0'))
        )
        
        self.input_data = {}
        self.output_data = {}
        self.state_labels = {}  # Store references to state labels
        
        # Start Redis listener in background
        threading.Thread(target=self.redis.start_listener, args=({
            'sensors': self.handle_sensor_data,
            'outputs': self.handle_output_data,
            'system_config': self.handle_config,
            'commands': self.handle_command
        },), daemon=True).start()

    def handle_sensor_data(self, data: Dict[str, Any]) -> None:
        """Handle incoming sensor data"""
        try:
            if 'samples' in data:
                for channel, channel_data in data['samples'].items():
                    if channel_data.get('metadata', {}).get('io_type') == 'input':
                        self.input_data[channel] = channel_data
                        logger.debug(f"Updated input {channel}: {channel_data}")
        except Exception as e:
            logger.error(f"Error handling sensor data: {e}")

    def handle_output_data(self, data: Dict[str, Any]) -> None:
        """Handle incoming output data"""
        try:
            if 'samples' in data:
                for channel, channel_data in data['samples'].items():
                    if channel_data.get('metadata', {}).get('io_type') == 'output':
                        self.output_data[channel] = channel_data
                        logger.debug(f"Updated output {channel}: {channel_data}")
        except Exception as e:
            logger.error(f"Error handling output data: {e}")

    def handle_config(self, data: Dict[str, Any]) -> None:
        """Handle system configuration updates"""
        try:
            if data.get('type') == 'eni_config':
                logger.info("Updated system configuration")
        except Exception as e:
            logger.error(f"Error handling config: {e}")

    def handle_command(self, data: Dict[str, Any]) -> None:
        """Handle command confirmations"""
        logger.info(f"Received command confirmation: {data}")

    def setup_page(self):
        """Set up the main page"""
        @ui.page('/')
        def home():
            with ui.column().classes('w-full max-w-[1200px] mx-auto p-4 mt-8 mb-16'):
                # Header
                with ui.row().classes('w-full items-center justify-between mb-6 bg-[#112240] p-4 rounded-lg'):
                    ui.label('Digital Output Controls').classes('text-2xl font-bold text-[#64ffda]')

                # Control panel
                with ui.card().classes('w-full p-4 bg-[#112240] rounded-lg'):
                    # Grid for control buttons
                    with ui.grid(columns=2).classes('w-full gap-4'):
                        # Create controls for each digital output
                        for channel in sorted(self.output_data.keys()):
                            if 'digital' in channel and 'output' in channel:
                                with ui.card().classes('p-4 bg-[#1d4f76] rounded-lg'):
                                    ui.label(channel).classes('mb-2 text-[#ccd6f6] font-mono')
                                    
                                    with ui.row().classes('gap-2 justify-center'):
                                        def make_handler(ch: str, val: float):
                                            return lambda: self.redis.publish_command(ch, val, 'digital')
                                        
                                        ui.button('ON', on_click=make_handler(channel, 1.0))\
                                            .props('flat dense').classes('bg-green-600 hover:bg-green-700')
                                        ui.button('OFF', on_click=make_handler(channel, 0.0))\
                                            .props('flat dense').classes('bg-red-600 hover:bg-red-700')
                                    
                                    # Create and store state label
                                    self.state_labels[channel] = ui.label('Current: --')\
                                        .classes('mt-2 text-[#8892b0] text-sm')

                def update_states():
                    """Update the states of all outputs"""
                    try:
                        for channel, label in self.state_labels.items():
                            if channel in self.output_data:
                                state = 'ON' if self.output_data[channel].get('value', 0) > 0.5 else 'OFF'
                                label.text = f'Current: {state}'
                    except Exception as e:
                        logger.error(f"Error updating states: {e}")

                # Update timer
                ui.timer(REFRESH_RATE, update_states)

def main():
    ui_app = UI()
    ui_app.setup_page()
    ui.run(
        port=int(os.getenv('UI_PORT', '8081')),
        title='EtherCAT I/O Monitor',
        reload=False
    )

if __name__ == '__main__':
    main() 