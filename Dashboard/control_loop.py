"""
X-Ray Tube Control Loop Module
Handles tube current/voltage control and filament monitoring
"""

import time
import threading
import logging
from datetime import datetime

class XRayControlLoop:
    def __init__(self):
        self.is_initialized = False
        self.is_running = False
        self.control_thread = None
        self.lock = threading.Lock()
        
        # Control parameters (input)
        self.target_tube_current = 0.0  # mA
        self.target_tube_voltage = 0.0  # kV
        
        # Display parameters (output/feedback)
        self.actual_filament_current = 0.0  # A
        self.actual_filament_voltage = 0.0  # V
        self.actual_tube_current = 0.0  # mA
        self.actual_tube_voltage = 0.0  # kV
        
        # System status
        self.last_update = datetime.now()
        self.error_message = None
        
        # Safety limits
        self.max_tube_current = 500.0  # mA
        self.max_tube_voltage = 150.0  # kV
        self.max_filament_current = 5.0  # A
        self.max_filament_voltage = 12.0  # V
        
        self._initialize_system()
    
    def _initialize_system(self):
        """Initialize the control system"""
        try:
            # Initialize hardware connections here
            # For now, simulate successful initialization
            self.is_initialized = True
            logging.info("X-Ray control system initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize X-Ray control system: {e}")
            self.error_message = str(e)
    
    def start_control_loop(self):
        """Start the control loop in a background thread"""
        if not self.is_initialized:
            return False
        
        if self.is_running:
            return True
        
        self.is_running = True
        self.control_thread = threading.Thread(target=self._control_loop, daemon=True)
        self.control_thread.start()
        logging.info("X-Ray control loop started")
        return True
    
    def stop_control_loop(self):
        """Stop the control loop"""
        self.is_running = False
        if self.control_thread:
            self.control_thread.join(timeout=2.0)
        logging.info("X-Ray control loop stopped")
    
    def _control_loop(self):
        """Main control loop - runs continuously"""
        while self.is_running:
            try:
                with self.lock:
                    # Simulate control logic
                    self._update_control_parameters()
                    self._read_feedback_values()
                    self.last_update = datetime.now()
                
                # Control loop frequency - 10Hz
                time.sleep(0.1)
                
            except Exception as e:
                logging.error(f"Error in control loop: {e}")
                self.error_message = str(e)
                time.sleep(1.0)
    
    def _update_control_parameters(self):
        """Update control outputs based on target values"""
        # Simulate control algorithm
        # In real implementation, this would interface with hardware
        
        # Simple simulation: filament parameters follow tube parameters
        # Typical X-ray tube relationships (simplified)
        if self.target_tube_voltage > 0:
            # Filament voltage typically 10-12V for tungsten filaments
            self.actual_filament_voltage = min(10.0 + (self.target_tube_voltage / 150.0) * 2.0, self.max_filament_voltage)
        else:
            self.actual_filament_voltage = 0.0
        
        if self.target_tube_current > 0:
            # Filament current relationship (simplified)
            self.actual_filament_current = min(2.0 + (self.target_tube_current / 500.0) * 3.0, self.max_filament_current)
        else:
            self.actual_filament_current = 0.0
    
    def _read_feedback_values(self):
        """Read actual tube parameters from hardware"""
        # Simulate feedback with some variation
        import random
        
        # Simulate actual values with small variations from targets
        if self.target_tube_voltage > 0:
            variation = random.uniform(-0.02, 0.02)  # ±2% variation
            self.actual_tube_voltage = self.target_tube_voltage * (1 + variation)
        else:
            self.actual_tube_voltage = 0.0
        
        if self.target_tube_current > 0:
            variation = random.uniform(-0.05, 0.05)  # ±5% variation
            self.actual_tube_current = self.target_tube_current * (1 + variation)
        else:
            self.actual_tube_current = 0.0
    
    def set_tube_parameters(self, current_ma, voltage_kv):
        """Set target tube current and voltage"""
        with self.lock:
            # Apply safety limits
            self.target_tube_current = max(0, min(current_ma, self.max_tube_current))
            self.target_tube_voltage = max(0, min(voltage_kv, self.max_tube_voltage))
            
            logging.info(f"Set tube parameters: {self.target_tube_current}mA, {self.target_tube_voltage}kV")
        
        return True
    
    def get_all_parameters(self):
        """Get all current parameters"""
        with self.lock:
            return {
                'targets': {
                    'tube_current': self.target_tube_current,
                    'tube_voltage': self.target_tube_voltage
                },
                'actuals': {
                    'tube_current': round(self.actual_tube_current, 2),
                    'tube_voltage': round(self.actual_tube_voltage, 2),
                    'filament_current': round(self.actual_filament_current, 3),
                    'filament_voltage': round(self.actual_filament_voltage, 2)
                },
                'limits': {
                    'max_tube_current': self.max_tube_current,
                    'max_tube_voltage': self.max_tube_voltage,
                    'max_filament_current': self.max_filament_current,
                    'max_filament_voltage': self.max_filament_voltage
                },
                'status': {
                    'initialized': self.is_initialized,
                    'running': self.is_running,
                    'last_update': self.last_update.isoformat(),
                    'error': self.error_message
                }
            }
    
    def emergency_stop(self):
        """Emergency stop - set all parameters to zero"""
        with self.lock:
            self.target_tube_current = 0.0
            self.target_tube_voltage = 0.0
            logging.warning("Emergency stop activated")
        return True
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.stop_control_loop() 