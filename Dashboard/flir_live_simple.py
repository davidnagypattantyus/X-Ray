import PySpin
import numpy as np
import cv2
import threading
import time
import os
from datetime import datetime
from pathlib import Path
import base64
import io

class FlirLiveCamera:
    def __init__(self):
        self.system = None
        self.cam = None
        self.nodemap = None
        self.is_initialized = False
        self.latest_image = None
        self.latest_image_data = None
        self.latest_histogram = None
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
            
            # Configure camera for single shot capture
            self._configure_camera()
            
            self.is_initialized = True
            print("Camera initialized successfully for manual exposures")
        except Exception as e:
            print(f"Error initializing camera: {e}")
            raise
    
    def _configure_camera(self):
        """Configure camera settings for single shot capture"""
        try:
            # Set acquisition mode to single frame
            if self.cam.AcquisitionMode.GetAccessMode() == PySpin.RW:
                self.cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_SingleFrame)
            
            # Set resolution to full vertical with 1:1 aspect ratio
            if self.cam.Width.GetAccessMode() == PySpin.RW and self.cam.Height.GetAccessMode() == PySpin.RW:
                # Get maximum height (full vertical resolution)
                max_height = self.cam.Height.GetMax()
                
                # Set width equal to height for 1:1 aspect ratio
                target_width = max_height
                
                # Ensure proper alignment
                width_inc = self.cam.Width.GetInc()
                height_inc = self.cam.Height.GetInc()
                
                # Align dimensions to camera requirements
                width = (target_width // width_inc) * width_inc
                height = (max_height // height_inc) * height_inc
                
                # Make sure width doesn't exceed maximum width
                max_width = self.cam.Width.GetMax()
                if width > max_width:
                    width = (max_width // width_inc) * width_inc
                    # Adjust height to maintain 1:1 ratio if needed
                    height = (width // height_inc) * height_inc
                
                self.cam.Width.SetValue(width)
                self.cam.Height.SetValue(height)
                print(f"Set capture resolution (1:1 aspect ratio): {width} x {height}")
            
            # Set default exposure time
            if self.cam.ExposureTime.GetAccessMode() == PySpin.RW:
                self.cam.ExposureTime.SetValue(50000)  # 50ms default (50000 microseconds)
            
            # Set default gain (ISO 100 equivalent)
            if self.cam.Gain.GetAccessMode() == PySpin.RW:
                self.cam.Gain.SetValue(0.0)  # Start with minimum gain
            
        except PySpin.SpinnakerException as e:
            print(f"Warning: Could not configure camera: {e}")
    
    def iso_to_gain(self, iso_value):
        """Convert ISO value to camera gain"""
        # ISO to gain conversion (approximate)
        # ISO 100 = 0dB, each doubling of ISO adds ~6dB of gain
        # This is camera-specific, but this gives a reasonable approximation
        iso_base = 100
        if iso_value < iso_base:
            iso_value = iso_base
        
        gain_db = 20 * np.log10(iso_value / iso_base)
        return max(0.0, min(20.0, gain_db))  # Clamp between 0-20dB
    
    def gain_to_iso(self, gain_db):
        """Convert camera gain to approximate ISO value"""
        iso_base = 100
        iso_value = iso_base * (10 ** (gain_db / 20))
        return int(round(iso_value))
    
    def capture_single_image(self):
        """Capture a single image manually"""
        if not self.is_initialized:
            return False
        
        try:
            # Begin acquisition for single frame
            self.cam.BeginAcquisition()
            
            # Capture image with timeout
            image_result = self.cam.GetNextImage(5000)  # 5 second timeout
            
            if not image_result.IsIncomplete():
                # Convert to numpy array
                image_data = image_result.GetNDArray()
                
                # Convert to 8-bit if needed
                if image_data.dtype != np.uint8:
                    # Normalize to 8-bit
                    image_data = ((image_data - image_data.min()) / 
                                (image_data.max() - image_data.min()) * 255).astype(np.uint8)
                
                # Convert to RGB using OpenCV
                if len(image_data.shape) == 2:
                    # Grayscale image - convert to RGB for web display
                    rgb_image = cv2.cvtColor(image_data, cv2.COLOR_GRAY2RGB)
                else:
                    # Color image
                    rgb_image = image_data
                
                # Encode as JPEG for web display using OpenCV
                success, img_encoded = cv2.imencode('.jpg', rgb_image, [cv2.IMWRITE_JPEG_QUALITY, 85])
                if success:
                    img_base64 = base64.b64encode(img_encoded.tobytes()).decode('utf-8')
                else:
                    img_base64 = None
                
                # Generate histogram for display
                histogram_data = self._generate_histogram(image_data)
                
                # Store the latest image
                with self.lock:
                    self.latest_image = img_base64
                    self.latest_image_data = image_data.copy()
                    self.latest_histogram = histogram_data
                
                success = True
            else:
                print(f"Image incomplete: {image_result.GetImageStatus()}")
                success = False
            
            # Release image and end acquisition
            image_result.Release()
            self.cam.EndAcquisition()
            
            return success
            
        except PySpin.SpinnakerException as e:
            print(f"Capture error: {e}")
            try:
                self.cam.EndAcquisition()
            except:
                pass
            return False
        except Exception as e:
            print(f"Unexpected error during capture: {e}")
            return False
    
    def get_latest_image(self):
        """Get the latest captured image as base64 string"""
        with self.lock:
            return self.latest_image
    
    def get_latest_histogram(self):
        """Get the latest histogram data"""
        with self.lock:
            return self.latest_histogram
    
    def _generate_histogram(self, image_data):
        """Generate histogram data from image using OpenCV"""
        try:
            # Calculate histogram for grayscale image (use the original grayscale data)
            if len(image_data.shape) == 3:
                # Convert to grayscale if color
                gray_image = cv2.cvtColor(image_data, cv2.COLOR_RGB2GRAY)
            else:
                gray_image = image_data
            
            # Calculate histogram - 256 bins for 8-bit image
            hist = cv2.calcHist([gray_image], [0], None, [256], [0, 256])
            
            # Convert to list for JSON serialization and flatten
            hist_list = hist.flatten().tolist()
            
            # Create bins array (0-255)
            bins = list(range(256))
            
            return {
                'bins': bins,
                'values': hist_list,
                'total_pixels': int(gray_image.size),
                'min_value': int(gray_image.min()),
                'max_value': int(gray_image.max()),
                'mean_value': float(gray_image.mean())
            }
        except Exception as e:
            print(f"Error generating histogram: {e}")
            return None
    
    def clear_image(self):
        """Clear the current image"""
        with self.lock:
            self.latest_image = None
            self.latest_image_data = None
            self.latest_histogram = None
    
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
                
                # Save as JPEG using OpenCV
                cv2.imwrite(filepath, self.latest_image_data, [cv2.IMWRITE_JPEG_QUALITY, 95])
                
                return filename
            except Exception as e:
                print(f"Error saving image: {e}")
                return None
    
    def set_exposure(self, exposure_ms):
        """Set exposure time in milliseconds"""
        try:
            # Convert ms to microseconds for camera
            exposure_us = exposure_ms * 1000
            if self.cam.ExposureTime.GetAccessMode() == PySpin.RW:
                self.cam.ExposureTime.SetValue(float(exposure_us))
                return True
        except Exception as e:
            print(f"Error setting exposure: {e}")
        return False
    
    def set_iso(self, iso_value):
        """Set ISO value (converts to gain internally)"""
        try:
            gain_db = self.iso_to_gain(iso_value)
            if self.cam.Gain.GetAccessMode() == PySpin.RW:
                self.cam.Gain.SetValue(gain_db)
                return True
        except Exception as e:
            print(f"Error setting ISO: {e}")
        return False
    
    def set_gain(self, gain_value):
        """Set camera gain directly"""
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
                gain_db = self.cam.Gain.GetValue()
                settings['gain'] = gain_db
                settings['iso'] = self.gain_to_iso(gain_db)
            if self.cam.ExposureTime.GetAccessMode() == PySpin.RW:
                # Convert microseconds to milliseconds for display
                exposure_us = self.cam.ExposureTime.GetValue()
                settings['exposure'] = exposure_us / 1000
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
        try:
            if self.cam:
                if self.cam.IsStreaming():
                    self.cam.EndAcquisition()
                self.cam.DeInit()
                del self.cam
            if self.system:
                self.system.ReleaseInstance()
        except Exception as e:
            print(f"Error cleaning up camera: {e}") 