from nicegui import ui
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class IOTable:
    """Component for displaying I/O data in a table format"""
    
    def __init__(self, title: str = "I/O Data"):
        self.title = title
        self.data = {}
        self.table = None
        self.container = None
        
    def create(self) -> ui.element:
        """Create the table component"""
        with ui.card().classes('w-full p-4 bg-[#112240] rounded-lg') as self.container:
            ui.label(self.title).classes('text-xl font-bold text-[#64ffda] mb-4')
            
            # Create table columns
            columns = [
                {'name': 'channel', 'label': 'Channel', 'field': 'channel', 'required': True, 'align': 'left'},
                {'name': 'value', 'label': 'Value', 'field': 'value', 'align': 'center'},
                {'name': 'type', 'label': 'Type', 'field': 'type', 'align': 'center'},
                {'name': 'io_type', 'label': 'I/O Type', 'field': 'io_type', 'align': 'center'},
                {'name': 'status', 'label': 'Status', 'field': 'status', 'align': 'center'},
            ]
            
            self.table = ui.table(
                columns=columns,
                rows=[],
                row_key='channel'
            ).classes('w-full bg-[#1d4f76]')
            
        return self.container
    
    def update_data(self, data: Dict[str, Any]):
        """Update the table data"""
        if not self.table:
            return
            
        self.data = data
        rows = []
        
        for channel, channel_data in data.items():
            try:
                metadata = channel_data.get('metadata', {})
                value = channel_data.get('value', 0)
                
                # Format value based on type
                value_type = metadata.get('value_type', 'FLOAT')
                if value_type == 'DIGITAL':
                    formatted_value = 'ON' if bool(value) else 'OFF'
                    status = 'Active' if bool(value) else 'Inactive'
                else:
                    formatted_value = f"{value:.3f}"
                    status = 'Normal'
                
                row = {
                    'channel': channel,
                    'value': formatted_value,
                    'type': metadata.get('type', 'unknown'),
                    'io_type': metadata.get('io_type', 'unknown'),
                    'status': status
                }
                rows.append(row)
                
            except Exception as e:
                logger.error(f"Error processing channel {channel}: {e}")
                
        # Update table rows
        self.table.rows = rows
        self.table.update()

class StatusIndicator:
    """Component for showing status indicators"""
    
    def __init__(self, label: str, initial_status: str = 'unknown'):
        self.label = label
        self.status = initial_status
        self.indicator = None
        
    def create(self) -> ui.element:
        """Create the status indicator"""
        with ui.row().classes('items-center gap-2') as container:
            ui.label(self.label).classes('text-[#ccd6f6]')
            self.indicator = ui.badge('', color='gray').classes('rounded-full')
            
        self.update_status(self.status)
        return container
    
    def update_status(self, status: str):
        """Update the status indicator"""
        if not self.indicator:
            return
            
        self.status = status
        
        if status == 'up' or status == 'online':
            self.indicator.props('color=green')
            self.indicator.text = 'Online'
        elif status == 'down' or status == 'offline':
            self.indicator.props('color=red') 
            self.indicator.text = 'Offline'
        elif status == 'warning':
            self.indicator.props('color=orange')
            self.indicator.text = 'Warning'
        else:
            self.indicator.props('color=gray')
            self.indicator.text = 'Unknown'

class ControlPanel:
    """Component for control buttons and inputs"""
    
    def __init__(self, title: str = "Controls"):
        self.title = title
        self.controls = {}
        self.container = None
        
    def create(self) -> ui.element:
        """Create the control panel"""
        with ui.card().classes('w-full p-4 bg-[#112240] rounded-lg') as self.container:
            ui.label(self.title).classes('text-xl font-bold text-[#64ffda] mb-4')
            self.controls_container = ui.column().classes('w-full gap-2')
            
        return self.container
    
    def add_digital_control(self, channel: str, on_change_callback=None):
        """Add a digital output control"""
        with self.controls_container:
            with ui.row().classes('items-center justify-between p-2 bg-[#1d4f76] rounded'):
                ui.label(channel).classes('text-[#ccd6f6] font-mono')
                
                with ui.row().classes('gap-2'):
                    on_btn = ui.button('ON', on_click=lambda: self._handle_digital_command(channel, 1.0, on_change_callback))
                    on_btn.props('flat dense').classes('bg-green-600 hover:bg-green-700')
                    
                    off_btn = ui.button('OFF', on_click=lambda: self._handle_digital_command(channel, 0.0, on_change_callback))
                    off_btn.props('flat dense').classes('bg-red-600 hover:bg-red-700')
                    
                    status_label = ui.label('--').classes('text-[#8892b0] text-sm min-w-[60px]')
                    
                self.controls[channel] = {
                    'type': 'digital',
                    'on_button': on_btn,
                    'off_button': off_btn,
                    'status_label': status_label
                }
    
    def _handle_digital_command(self, channel: str, value: float, callback=None):
        """Handle digital control command"""
        if callback:
            callback(channel, value, 'digital')
    
    def update_control_status(self, channel: str, value: Any):
        """Update the status display for a control"""
        if channel in self.controls:
            control = self.controls[channel]
            if control['type'] == 'digital':
                status = 'ON' if bool(value) else 'OFF'
                control['status_label'].text = status 