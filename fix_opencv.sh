#!/bin/bash

echo "Fixing OpenCV installation for X-Ray Dashboard..."

# Navigate to Dashboard directory
cd /home/davidnagypattantyus/Desktop/repo/X-Ray/Dashboard

# Activate virtual environment
source camera_env/bin/activate

# Install OpenCV and dependencies
echo "Installing OpenCV and dependencies..."
pip install opencv-python scikit-image matplotlib

# Test the installation
echo "Testing OpenCV installation..."
python -c "import cv2; print('OpenCV installed successfully!')"

# Restart the service
echo "Restarting dashboard service..."
sudo systemctl restart xray-dashboard.service

echo "Waiting for service to start..."
sleep 5

# Check service status
systemctl status xray-dashboard.service --no-pager

echo "Fix complete! Check http://xraypi.local:8080/api/camera/status" 