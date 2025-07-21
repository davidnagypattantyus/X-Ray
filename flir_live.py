import PySpin
import numpy as np
import cv2
import threading
import time
import os
from datetime import datetime
from pathlib import Path
import base64

class FlirLiveCamera:
    def __init__(self):
        self.system = None
        self.cam = None
        self.nodemap = None
        self.is_streaming = False
        self.latest_image = None
        self.latest_image_data = None
        self.capture_thread = None
        self.lock = threading.Lock()
        self._initialize_camera()
    
    def _initialize_camera(self):
        """Initialize camera connection"""
        try:
            # Set USB memory if not already set
            usb_memory_path = "/sys/module/usbcore/parameters/usbfs_memory_mb"
            if os.path.exists(usb_memory_path):
                with open(usb_memory_path, 'r') as f:
                    current_memory = int(f.read().strip())
                    if current_memory < 256:
                        os.system('sudo sh -c "echo 256 > /sys/module/usbcore/parameters/usbfs_memory_mb"')
            
            self.system = PySpin.System.GetInstance()
            cam_list = self.system.GetCameras()
            
            if cam_list.GetSize() == 0:
                raise RuntimeError("No cameras found!")
            
            self.cam = cam_list[0]
            self.cam.Init()
            self.nodemap = self.cam.GetNodeMap()
            
            # Configure camera for optimal performance
            self._configure_camera()
            
            print("Camera initialized successfully")
        except Exception as e:
            print(f"Error initializing camera: {e}")
            raise
    
    def _configure_camera(self):
        """Configure camera settings for live streaming"""
        try:
            # Set acquisition mode to continuous
            if self.cam.AcquisitionMode.GetAccessMode() == PySpin.RW:
                self.cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_Continuous)
            
            # Set a reasonable resolution for live streaming
            if self.cam.Width.GetAccessMode() == PySpin.RW and self.cam.Height.GetAccessMode() == PySpin.RW:
                # Set to 1/4 resolution for faster streaming
                max_width = self.cam.Width.GetMax()
                max_height = self.cam.Height.GetMax()
                
                new_width = max_width // 4
                new_height = max_height // 4
                
                # Ensure proper alignment
                width_inc = self.cam.Width.GetInc()
                height_inc = self.cam.Height.GetInc()
                new_width = (new_width // width_inc) * width_inc
                new_height = (new_height // height_inc) * height_inc
                
                self.cam.Width.SetValue(new_width)
                self.cam.Height.SetValue(new_height)
                print(f"Set streaming resolution: {new_width} x {new_height}")
            
            # Set exposure time for reasonable frame rate
            if self.cam.ExposureTime.GetAccessMode() == PySpin.RW:
                self.cam.ExposureTime.SetValue(20000)  # 20ms
            
            # Set gain
            if self.cam.Gain.GetAccessMode() == PySpin.RW:
                self.cam.Gain.SetValue(1.0)
            
        except PySpin.SpinnakerException as e:
            print(f"Warning: Could not configure camera: {e}")
    
    def start_streaming(self):
        """Start continuous image capture"""
        if self.is_streaming:
            return
        
        try:
            self.cam.BeginAcquisition()
            self.is_streaming = True
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            print("Live streaming started")
        except Exception as e:
            print(f"Error starting streaming: {e}")
    
    def stop_streaming(self):
        """Stop continuous image capture"""
        if not self.is_streaming:
            return
        
        self.is_streaming = False
        
        try:
            if self.cam and self.cam.IsStreaming():
                self.cam.EndAcquisition()
            print("Live streaming stopped")
        except Exception as e:
            print(f"Error stopping streaming: {e}")
    
    def _capture_loop(self):
        """Main capture loop that runs every 5 seconds"""
        while self.is_streaming:
            try:
                # Capture image
                image_result = self.cam.GetNextImage(1000)
                
                if not image_result.IsIncomplete():
                    # Convert to numpy array
                    image_data = image_result.GetNDArray()
                    
                    # Convert to 8-bit if needed
                    if image_data.dtype != np.uint8:
                        # Normalize to 8-bit
                        image_data = ((image_data - image_data.min()) / 
                                    (image_data.max() - image_data.min()) * 255).astype(np.uint8)
                    
                    # Convert grayscale to RGB for web display
                    if len(image_data.shape) == 2:
                        image_rgb = cv2.cvtColor(image_data, cv2.COLOR_GRAY2RGB)
                    else:
                        image_rgb = image_data
                    
                    # Encode as JPEG for web display
                    _, buffer = cv2.imencode('.jpg', image_rgb, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    img_base64 = base64.b64encode(buffer).decode('utf-8')
                    
                    # Store the latest image
                    with self.lock:
                        self.latest_image = img_base64
                        self.latest_image_data = image_data.copy()
                
                image_result.Release()
                
                # Wait 5 seconds before next capture
                time.sleep(5)
                
            except PySpin.SpinnakerException as e:
                print(f"Capture error: {e}")
                time.sleep(1)
            except Exception as e:
                print(f"Unexpected error in capture loop: {e}")
                break
    
    def get_latest_image(self):
        """Get the latest captured image as base64 string"""
        with self.lock:
            return self.latest_image
    
    def save_current_image(self, save_path="/home/davidnagypattantyus/Desktop"):
        """Save the current image to desktop"""
        with self.lock:
            if self.latest_image_data is None:
                return None
            
            try:
                # Create filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"flir_capture_{timestamp}.jpg"
                filepath = os.path.join(save_path, filename)
                
                # Save as JPEG
                cv2.imwrite(filepath, self.latest_image_data)
                
                return filename
            except Exception as e:
                print(f"Error saving image: {e}")
                return None
    
    def set_exposure(self, exposure_us):
        """Set exposure time in microseconds"""
        try:
            if self.cam.ExposureTime.GetAccessMode() == PySpin.RW:
                self.cam.ExposureTime.SetValue(float(exposure_us))
                return True
        except Exception as e:
            print(f"Error setting exposure: {e}")
        return False
    
    def set_gain(self, gain_value):
        """Set camera gain"""
        try:
            if self.cam.Gain.GetAccessMode() == PySpin.RW:
                self.cam.Gain.SetValue(float(gain_value))
                return True
        except Exception as e:
            print(f"Error setting gain: {e}")
        return False
    
    def get_settings(self):
        """Get current camera settings"""
        try:
            settings = {}
            if self.cam.Gain.GetAccessMode() == PySpin.RW:
                settings['gain'] = self.cam.Gain.GetValue()
            if self.cam.ExposureTime.GetAccessMode() == PySpin.RW:
                settings['exposure'] = self.cam.ExposureTime.GetValue()
            if self.cam.Width.GetAccessMode() == PySpin.RW:
                settings['width'] = self.cam.Width.GetValue()
            if self.cam.Height.GetAccessMode() == PySpin.RW:
                settings['height'] = self.cam.Height.GetValue()
            return settings
        except Exception as e:
            print(f"Error getting settings: {e}")
            return {}
    
    def __del__(self):
        """Cleanup camera resources"""
        self.stop_streaming()
        try:
            if self.cam:
                self.cam.DeInit()
                del self.cam
            if self.system:
                self.system.ReleaseInstance()
        except Exception as e:
            print(f"Error cleaning up camera: {e}") 