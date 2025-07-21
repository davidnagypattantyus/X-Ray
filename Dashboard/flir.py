try:
    import PySpin
    PYSPIN_AVAILABLE = True
except ImportError:
    PySpin = None
    PYSPIN_AVAILABLE = False

import numpy as np
from pathlib import Path
import time
from datetime import datetime

class FlirCamera:
    def __init__(self):
        if not PYSPIN_AVAILABLE:
            raise RuntimeError("PySpin not available - FLIR camera functionality disabled")
        
        self.system = PySpin.System.GetInstance()
        self.cam = None
        self.nodemap = None
        self._connect_camera()
    
    def _connect_camera(self):
        """Initialize and connect to the first available camera"""
        try:
            # Get camera list
            cam_list = self.system.GetCameras()
            if cam_list.GetSize() == 0:
                raise RuntimeError("No cameras found!")
            
            self.cam = cam_list[0]
            self.cam.Init()
            self.nodemap = self.cam.GetNodeMap()
            
            # Enable continuous acquisition mode
            self.cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
            
            print("Camera initialized successfully")
        except PySpin.SpinnakerException as e:
            raise RuntimeError(f"Error initializing camera: {e}")
    
    def set_gain(self, gain_value):
        """Set camera gain"""
        try:
            if self.cam.GainAuto.GetAccessMode() == PySpin.RW:
                self.cam.GainAuto.SetValue(PySpin.GainAuto_Off)
            
            if self.cam.Gain.GetAccessMode() == PySpin.RW:
                gain_value = float(gain_value)
                self.cam.Gain.SetValue(gain_value)
                return True
        except PySpin.SpinnakerException as e:
            print(f"Error setting gain: {e}")
            return False
    
    def set_exposure_time(self, exposure_time_us):
        """Set exposure time in microseconds"""
        try:
            if self.cam.ExposureAuto.GetAccessMode() == PySpin.RW:
                self.cam.ExposureAuto.SetValue(PySpin.ExposureAuto_Off)
            
            if self.cam.ExposureTime.GetAccessMode() == PySpin.RW:
                exposure_time_us = float(exposure_time_us)
                self.cam.ExposureTime.SetValue(exposure_time_us)
                return True
        except PySpin.SpinnakerException as e:
            print(f"Error setting exposure time: {e}")
            return False
    
    def set_roi(self, width, height, offset_x=0, offset_y=0):
        """Set Region of Interest (ROI)"""
        try:
            # Ensure acquisition is stopped
            self.cam.BeginAcquisition() if not self.cam.IsStreaming() else None
            self.cam.EndAcquisition()
            
            # Set width
            if self.cam.Width.GetAccessMode() == PySpin.RW:
                width = int(width)
                width_inc = self.cam.Width.GetInc()
                width_adjusted = (width // width_inc) * width_inc
                self.cam.Width.SetValue(width_adjusted)
            
            # Set height
            if self.cam.Height.GetAccessMode() == PySpin.RW:
                height = int(height)
                height_inc = self.cam.Height.GetInc()
                height_adjusted = (height // height_inc) * height_inc
                self.cam.Height.SetValue(height_adjusted)
            
            # Set offsets
            if self.cam.OffsetX.GetAccessMode() == PySpin.RW:
                self.cam.OffsetX.SetValue(int(offset_x))
            if self.cam.OffsetY.GetAccessMode() == PySpin.RW:
                self.cam.OffsetY.SetValue(int(offset_y))
            
            return True
        except PySpin.SpinnakerException as e:
            print(f"Error setting ROI: {e}")
            return False
    
    def capture_image(self, save_path="Dashboard/static/captures"):
        """Capture a single image and save it as TIFF"""
        try:
            # Create save directory if it doesn't exist
            Path(save_path).mkdir(parents=True, exist_ok=True)
            
            # Start acquisition
            self.cam.BeginAcquisition() if not self.cam.IsStreaming() else None
            
            # Get image
            image_result = self.cam.GetNextImage(1000)
            
            if image_result.IsIncomplete():
                print("Image incomplete with status", image_result.GetImageStatus())
                return None
            
            # Convert to numpy array
            image_data = image_result.GetNDArray()
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"capture_{timestamp}.tiff"
            filepath = str(Path(save_path) / filename)
            
            # Save image
            image_result.Save(filepath)
            
            # Release image
            image_result.Release()
            
            # End acquisition
            self.cam.EndAcquisition()
            
            return filename
        except PySpin.SpinnakerException as e:
            print(f"Error capturing image: {e}")
            return None
    
    def get_current_settings(self):
        """Get current camera settings"""
        try:
            settings = {
                'gain': self.cam.Gain.GetValue(),
                'exposure_time': self.cam.ExposureTime.GetValue(),
                'width': self.cam.Width.GetValue(),
                'height': self.cam.Height.GetValue(),
                'offset_x': self.cam.OffsetX.GetValue(),
                'offset_y': self.cam.OffsetY.GetValue()
            }
            return settings
        except PySpin.SpinnakerException as e:
            print(f"Error getting settings: {e}")
            return None
    
    def __del__(self):
        """Cleanup camera resources"""
        try:
            if self.cam:
                self.cam.EndAcquisition() if self.cam.IsStreaming() else None
                self.cam.DeInit()
                del self.cam
            
            if self.system:
                self.system.ReleaseInstance()
        except PySpin.SpinnakerException as e:
            print(f"Error cleaning up camera: {e}") 