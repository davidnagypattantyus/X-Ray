#!/usr/bin/env python3
"""
Simple FLIR camera test script
This script will test the camera connection and basic functionality
"""

import sys
import time
import os
from datetime import datetime

try:
    import PySpin
    print("✓ PySpin imported successfully")
    PYSPIN_AVAILABLE = True
except ImportError as e:
    print(f"✗ PySpin import failed: {e}")
    PYSPIN_AVAILABLE = False

def configure_usb_settings():
    """Configure USB settings for better performance"""
    try:
        # Try to increase USB memory limits
        usb_memory_path = "/sys/module/usbcore/parameters/usbfs_memory_mb"
        if os.path.exists(usb_memory_path):
            with open(usb_memory_path, 'r') as f:
                current_memory = f.read().strip()
                print(f"Current USB memory limit: {current_memory} MB")
                
                # Suggest increasing if it's too low
                if int(current_memory) < 256:
                    print("⚠️  USB memory limit is low. Consider running:")
                    print("   sudo sh -c 'echo 256 > /sys/module/usbcore/parameters/usbfs_memory_mb'")
    except Exception as e:
        print(f"Could not check USB settings: {e}")

def test_camera_connection():
    """Test basic camera connection"""
    if not PYSPIN_AVAILABLE:
        print("PySpin not available, cannot test camera")
        return False
    
    try:
        # Initialize system
        system = PySpin.System.GetInstance()
        print("✓ Spinnaker system initialized")
        
        # Get camera list
        cam_list = system.GetCameras()
        num_cameras = cam_list.GetSize()
        
        print(f"Found {num_cameras} camera(s)")
        
        if num_cameras == 0:
            print("✗ No cameras detected")
            cam_list.Clear()
            system.ReleaseInstance()
            return False
        
        # Get first camera
        cam = cam_list[0]
        print("✓ Camera object created")
        
        # Initialize camera
        cam.Init()
        print("✓ Camera initialized")
        
        # Get device info
        nodemap = cam.GetNodeMap()
        device_vendor = PySpin.CStringPtr(nodemap.GetNode('DeviceVendorName'))
        device_model = PySpin.CStringPtr(nodemap.GetNode('DeviceModelName'))
        device_serial = PySpin.CStringPtr(nodemap.GetNode('DeviceSerialNumber'))
        
        if PySpin.IsReadable(device_vendor):
            print(f"Vendor: {device_vendor.GetValue()}")
        if PySpin.IsReadable(device_model):
            print(f"Model: {device_model.GetValue()}")
        if PySpin.IsReadable(device_serial):
            print(f"Serial: {device_serial.GetValue()}")
        
        # Test basic settings
        try:
            # Set smaller image size to reduce memory requirements
            if cam.Width.GetAccessMode() == PySpin.RW and cam.Height.GetAccessMode() == PySpin.RW:
                max_width = cam.Width.GetMax()
                max_height = cam.Height.GetMax()
                
                # Set to half resolution to reduce memory usage
                new_width = max_width // 2
                new_height = max_height // 2
                
                # Ensure width/height are properly aligned
                width_inc = cam.Width.GetInc()
                height_inc = cam.Height.GetInc()
                new_width = (new_width // width_inc) * width_inc
                new_height = (new_height // height_inc) * height_inc
                
                cam.Width.SetValue(new_width)
                cam.Height.SetValue(new_height)
                
                print(f"Set image size: {new_width} x {new_height} (reduced from {max_width} x {max_height})")
            
            # Get current gain
            if cam.Gain.GetAccessMode() == PySpin.RW:
                current_gain = cam.Gain.GetValue()
                print(f"Current gain: {current_gain}")
            
            # Get current exposure
            if cam.ExposureTime.GetAccessMode() == PySpin.RW:
                current_exposure = cam.ExposureTime.GetValue()
                print(f"Current exposure: {current_exposure} μs")
            
            # Get image dimensions
            width = cam.Width.GetValue()
            height = cam.Height.GetValue()
            print(f"Current image size: {width} x {height}")
            
        except PySpin.SpinnakerException as e:
            print(f"Warning: Could not configure camera settings: {e}")
        
        # Cleanup
        cam.DeInit()
        del cam
        cam_list.Clear()
        system.ReleaseInstance()
        
        print("✓ Camera test completed successfully")
        return True
        
    except PySpin.SpinnakerException as e:
        print(f"✗ Spinnaker error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def capture_test_image():
    """Capture a test image"""
    if not PYSPIN_AVAILABLE:
        print("PySpin not available, cannot capture image")
        return False
    
    try:
        system = PySpin.System.GetInstance()
        cam_list = system.GetCameras()
        
        if cam_list.GetSize() == 0:
            print("No cameras available for image capture")
            return False
        
        cam = cam_list[0]
        cam.Init()
        
        # Configure for lower memory usage
        try:
            # Set to smaller resolution
            if cam.Width.GetAccessMode() == PySpin.RW and cam.Height.GetAccessMode() == PySpin.RW:
                max_width = cam.Width.GetMax()
                max_height = cam.Height.GetMax()
                
                new_width = min(640, max_width)
                new_height = min(480, max_height)
                
                # Ensure proper alignment
                width_inc = cam.Width.GetInc()
                height_inc = cam.Height.GetInc()
                new_width = (new_width // width_inc) * width_inc
                new_height = (new_height // height_inc) * height_inc
                
                cam.Width.SetValue(new_width)
                cam.Height.SetValue(new_height)
                print(f"Set capture size: {new_width} x {new_height}")
            
            # Set lower exposure for faster capture
            if cam.ExposureTime.GetAccessMode() == PySpin.RW:
                cam.ExposureTime.SetValue(10000)  # 10ms
        
        except Exception as e:
            print(f"Warning: Could not optimize settings: {e}")
        
        # Set acquisition mode to single frame
        if cam.AcquisitionMode.GetAccessMode() == PySpin.RW:
            cam.AcquisitionMode.SetValue(PySpin.AcquisitionMode_SingleFrame)
        
        # Begin acquisition
        cam.BeginAcquisition()
        
        # Get image
        image_result = cam.GetNextImage(5000)  # 5 second timeout
        
        if image_result.IsIncomplete():
            print(f"Image incomplete: {image_result.GetImageStatus()}")
        else:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"test_capture_{timestamp}.jpg"
            
            # Save image
            image_result.Save(filename)
            print(f"✓ Image saved as {filename}")
            
            # Print image info
            print(f"Image dimensions: {image_result.GetWidth()} x {image_result.GetHeight()}")
            print(f"Pixel format: {image_result.GetPixelFormat()}")
        
        # Release image
        image_result.Release()
        
        # End acquisition
        cam.EndAcquisition()
        
        # Cleanup
        cam.DeInit()
        del cam
        cam_list.Clear()
        system.ReleaseInstance()
        
        return True
        
    except PySpin.SpinnakerException as e:
        print(f"✗ Error capturing image: {e}")
        return False

def main():
    """Main test function"""
    print("="*50)
    print("FLIR Camera Test Script")
    print("="*50)
    
    # Check USB configuration
    configure_usb_settings()
    
    # Test 1: Check PySpin import
    if not PYSPIN_AVAILABLE:
        print("Cannot proceed - PySpin not available")
        print("\nTo install Spinnaker SDK:")
        print("1. Download the ARM64 Ubuntu package from FLIR")
        print("2. Extract and install the .deb packages")
        print("3. Install the Python wheel package")
        return
    
    # Test 2: Camera connection
    print("\nTesting camera connection...")
    if not test_camera_connection():
        print("Camera connection test failed")
        return
    
    # Test 3: Image capture
    print("\nTesting image capture...")
    input("Press Enter to capture a test image (or Ctrl+C to skip)...")
    try:
        capture_test_image()
    except KeyboardInterrupt:
        print("Image capture skipped")
    
    print("\n" + "="*50)
    print("Test completed!")

if __name__ == "__main__":
    main() 