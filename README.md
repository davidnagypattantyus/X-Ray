# X-Ray Dashboard System

A comprehensive Flask-based web dashboard for FLIR Blackfly S camera control and X-ray tube control, designed for Raspberry Pi with remote access capabilities.

## 🏗️ System Architecture

### Core Components
- **Flask Web Application** (`Dashboard/app.py`) - Main dashboard server
- **FLIR Camera Interface** (`Dashboard/flir_live_simple.py`) - PySpin-based camera control
- **X-Ray Control Loop** (`Dashboard/control_loop.py`) - Tube current/voltage simulation
- **Web Templates** (`Dashboard/templates/`) - Modern dark-mode UI with DIN font
- **Systemd Service** - Auto-start on boot with proper permissions
- **Tailscale Integration** - Remote access via VPN
- **mDNS/Avahi** - Local hostname resolution (`xraypi.local`)

### Network Access Methods
1. **Local WiFi/Ethernet**: `http://192.168.x.x:8080`
2. **Direct Ethernet**: `http://xraypi.local:8080`
3. **Remote (Tailscale)**: `http://100.109.159.37:8080`

## 📋 Prerequisites

### Hardware
- Raspberry Pi 4 (ARM64)
- FLIR Blackfly S BFS-U3-200S6M camera
- USB 3.0 connection to camera
- Network connectivity (WiFi or Ethernet)

### Software Base
- Raspberry Pi OS (Debian 12 Bookworm, ARM64)
- Python 3.11
- Docker (optional, legacy)

## 🚀 Complete Installation Guide

### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3-venv python3-pip curl avahi-daemon avahi-utils udev

# Add user to required groups
sudo usermod -a -G plugdev,dialout,docker $USER

# Reboot to apply group changes
sudo reboot
```

### 2. USB Device Permissions

Create udev rules for FLIR camera access:

```bash
sudo nano /etc/udev/rules.d/40-flir-spinnaker.rules
```

Add content:
```
# FLIR USB3 cameras
SUBSYSTEM=="usb", ATTRS{idVendor}=="1e10", MODE="0666", GROUP="plugdev"
# FLIR USB2 cameras  
SUBSYSTEM=="usb", ATTRS{idVendor}=="1724", MODE="0666", GROUP="plugdev"
```

Apply rules:
```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
```

### 3. Spinnaker SDK Installation

The system includes pre-downloaded Spinnaker SDK files for ARM64:
- `Dashboard/spinnaker-4.2.0.88-arm64-22.04-pkg.tar` (47MB) - Main SDK
- `Dashboard/spinnaker_python-4.2.0.88-cp310-cp310-linux_aarch64.whl` (9.8MB) - Python bindings

#### Manual Installation Process:

```bash
# Navigate to Dashboard directory
cd Dashboard

# Extract and install Spinnaker SDK
tar -xf spinnaker-4.2.0.88-arm64-22.04-pkg.tar
cd spinnaker-4.2.0.88-arm64

# Install system packages
sudo dpkg -i libgentl_*.deb
sudo dpkg -i libspinnaker_*.deb
sudo dpkg -i libspinnaker-dev_*.deb
sudo dpkg -i libspinnaker-c_*.deb
sudo dpkg -i libspinnaker-c-dev_*.deb
sudo dpkg -i spinnaker_*.deb
sudo dpkg -i spinnaker-doc_*.deb

# Fix any dependency issues
sudo apt-get install -f

# Configure USB memory (required for high-speed cameras)
sudo sh -c 'echo 256 > /sys/module/usbcore/parameters/usbfs_memory_mb'
echo 'echo 256 > /sys/module/usbcore/parameters/usbfs_memory_mb' | sudo tee -a /etc/rc.local
```

### 4. Python Environment Setup

```bash
# Navigate to Dashboard directory
cd Dashboard

# Create virtual environment
python3 -m venv camera_env
source camera_env/bin/activate

# Install Python dependencies
pip install flask pillow numpy

# Install PySpin (requires manual extraction due to Python version mismatch)
# The wheel is built for Python 3.10, but we're using 3.11
python -m zipfile -e spinnaker_python-4.2.0.88-cp310-cp310-linux_aarch64.whl temp_wheel/

# Copy and rename the compiled module for Python 3.11
mkdir -p camera_env/lib/python3.11/site-packages/
cp -r temp_wheel/PySpin* camera_env/lib/python3.11/site-packages/
mv camera_env/lib/python3.11/site-packages/PySpin*.dist-info camera_env/lib/python3.11/site-packages/PySpin-4.2.0.88.dist-info
```

### 5. Systemd Service Configuration

Create service file:
```bash
sudo nano /etc/systemd/system/xray-dashboard.service
```

Content:
```ini
[Unit]
Description=X-Ray Dashboard Flask Application
After=network.target
Wants=network.target

[Service]
Type=simple
User=davidnagypattantyus
Group=davidnagypattantyus
WorkingDirectory=/home/davidnagypattantyus/Desktop/repo/X-Ray/Dashboard
ExecStart=/home/davidnagypattantyus/Desktop/repo/X-Ray/Dashboard/camera_env/bin/python app.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Allow access to USB devices for camera
SupplementaryGroups=plugdev dialout

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable xray-dashboard.service
sudo systemctl start xray-dashboard.service
```

### 6. Network Configuration

#### mDNS/Avahi Setup:
```bash
# Enable Avahi for local hostname resolution
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon
```

#### Tailscale Setup:
```bash
# Install Tailscale (if not already installed)
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate (follow prompts)
sudo tailscale up

# Enable auto-start
sudo systemctl enable tailscaled
```

## 🎛️ Dashboard Features

### Camera Control Interface (`/live-camera`)
- **Manual Capture**: Instant image capture with save functionality
- **ISO Control**: 100-3200 range with real-time adjustment
- **Exposure Control**: 10-200ms with precision timing
- **1:1 Aspect Ratio Display**: Full-frame 3648x3648 image viewing
- **Base64 JPEG Encoding**: Efficient web display
- **Auto-refresh Status**: 10-second interval camera status updates

### X-Ray Control Interface (`/control-loop`)
- **Tube Current Input**: Real-time current control (0-50mA)
- **Tube Voltage Input**: High-voltage control (10-150kV)
- **Filament Feedback**: Simulated filament current/voltage display
- **Safety Limits**: Built-in parameter validation
- **Threading**: Non-blocking control loop operation

### Technical Specifications
- **Camera Resolution**: 3648x3648 pixels
- **Image Format**: JPEG with base64 encoding
- **Exposure Range**: 10-200ms
- **ISO Range**: 100-3200
- **Web Framework**: Flask with debug mode
- **UI Theme**: Dark mode with grayscale DIN font styling

## 🔧 File Structure

```
X-Ray/
├── README.md                       # This comprehensive documentation
├── compose.yml                     # Docker Compose (legacy/alternative)
├── requirements.txt                # Python dependencies reference
├── Dockerfile.camera               # Docker setup (legacy/alternative)
└── Dashboard/                      # Main application directory
    ├── app.py                      # Main Flask application
    ├── flir_live_simple.py         # Camera interface module
    ├── control_loop.py             # X-ray control simulation
    ├── manage_dashboard.sh         # Service management script
    ├── camera_env/                 # Python virtual environment
    │   ├── bin/python              # Python interpreter
    │   └── lib/python3.11/site-packages/PySpin*  # Camera drivers
    ├── templates/
    │   ├── landing.html            # Main dashboard page
    │   ├── live_camera.html        # Camera control interface
    │   └── control_loop.html       # X-ray control interface
    ├── static/                     # CSS and assets
    ├── spinnaker-4.2.0.88-arm64-22.04-pkg.tar    # SDK installer
    └── spinnaker_python-4.2.0.88-cp310-cp310-linux_aarch64.whl  # Python bindings
```

## 🚨 Critical Dependencies

### System-Level:
- **PySpin Camera Drivers**: Installed via Spinnaker SDK
- **USB Permissions**: udev rules for camera access
- **USB Memory Buffer**: 256MB allocation for high-speed USB
- **Python 3.11**: Virtual environment with specific packages

### Python Packages:
- **Flask**: Web framework
- **PySpin**: FLIR camera control (manually installed)
- **Pillow**: Image processing (replaces OpenCV for compatibility)
- **NumPy**: Array operations (compatible version for PySpin)

### Service Dependencies:
- **Systemd Service**: Auto-start with proper user/group permissions
- **Avahi Daemon**: mDNS hostname resolution
- **Tailscale Daemon**: VPN connectivity

## 🔄 Service Management

Use the included management script:

```bash
# Navigate to Dashboard directory
cd Dashboard

# Check status
./manage_dashboard.sh status

# View logs
./manage_dashboard.sh logs

# Restart service
./manage_dashboard.sh restart

# Stop service
./manage_dashboard.sh stop

# Start service
./manage_dashboard.sh start
```

## 🌐 Network Access

### Local Network:
- **WiFi/Ethernet**: `http://[PI_IP]:8080`
- **Find IP**: `hostname -I` or `ip addr show`

### Direct Ethernet:
- **mDNS Hostname**: `http://xraypi.local:8080`
- **Requirements**: Avahi daemon running on Pi, mDNS support on client

### Remote Access:
- **Tailscale**: `http://100.109.159.37:8080`
- **Requirements**: Tailscale installed and authenticated on both devices

## 🔧 Troubleshooting

### Camera Not Detected:
```bash
# Check USB connection
lsusb | grep -i "1e10\|Point Grey"

# Verify permissions
ls -la /dev/bus/usb/*/[device_number]

# Reload udev rules
sudo udevadm control --reload-rules && sudo udevadm trigger

# Restart service
sudo systemctl restart xray-dashboard.service
```

### Service Issues:
```bash
# Check service status
systemctl status xray-dashboard.service

# View detailed logs
journalctl -u xray-dashboard.service -f

# Verify Python environment
/home/davidnagypattantyus/Desktop/repo/X-Ray/Dashboard/camera_env/bin/python -c "import PySpin; print('PySpin OK')"
```

### Network Issues:
```bash
# Test local access
curl -s http://localhost:8080/api/camera/status

# Test Tailscale
tailscale status

# Test mDNS
avahi-resolve-host-name xraypi.local
```

## 🔄 Replication on New Pi

### Quick Setup:
1. **Copy entire project directory** to new Pi
2. **Install system dependencies** (Section 1-2)
3. **Install Spinnaker SDK** using included tar file (Section 3)
4. **Update paths** in systemd service file for new user/location
5. **Configure udev rules** (Section 2)
6. **Enable services** (Section 5-6)

### Path Updates Required:
- Update `WorkingDirectory` and `ExecStart` in systemd service
- Update `User` and `Group` in systemd service
- Verify Python virtual environment paths

### Verification:
```bash
# Test camera detection
cd Dashboard
source camera_env/bin/activate
python -c "import PySpin; system = PySpin.System.GetInstance(); print(f'Cameras: {system.GetCameras().GetSize()}')"

# Test Flask app
python app.py
```

## 📊 Performance Notes

- **Boot Time**: ~30 seconds to full dashboard availability
- **Camera Initialization**: ~2-3 seconds after USB detection
- **Image Capture**: ~500ms for full resolution
- **Memory Usage**: ~150MB for Flask app + camera drivers
- **Network Latency**: <100ms on local network, varies on Tailscale

## 🛡️ Security Considerations

- **Local Network Only**: Flask debug mode should not be exposed to internet
- **Tailscale VPN**: Encrypted tunnel for remote access
- **USB Permissions**: Limited to plugdev group members
- **Service User**: Runs as non-root user with minimal privileges

## 📞 API Endpoints

### Camera API:
- `GET /api/camera/status` - Camera availability and settings
- `POST /api/camera/capture` - Trigger manual capture
- `POST /api/camera/settings` - Update ISO/exposure settings

### Control Loop API:
- `GET /api/control/status` - Current tube parameters
- `POST /api/control/update` - Update tube current/voltage
- `GET /api/control/filament` - Filament feedback values

## 🔄 Evolution Notes

This project has evolved from:
- **Phase 1**: Multi-service Docker setup with Redis, InfluxDB, Grafana
- **Phase 2**: Simplified Docker dashboard with USB device access  
- **Phase 3**: **Current** - Direct systemd service with Flask + PySpin integration

The current implementation prioritizes:
- **Reliability**: Systemd service management with auto-restart
- **Performance**: Direct hardware access without Docker overhead
- **Simplicity**: Single Flask application with embedded functionality
- **Accessibility**: Multiple network access methods for various use cases

### Alternative Deployment Options:
- **Docker**: Use `compose.yml` for containerized deployment
- **Manual**: Run Flask app directly for development/testing
- **Systemd**: Current production approach with auto-start

## 🎉 Quick Start

1. **Connect camera** via USB 3.0
2. **Check service**: `cd Dashboard && ./manage_dashboard.sh status`
3. **Access dashboard**: Navigate to `http://xraypi.local:8080`
4. **Use camera controls**: Go to `/live-camera` for manual capture
5. **Use X-ray controls**: Go to `/control-loop` for tube simulation

The system is designed to work immediately after boot with no manual intervention required.

---

*Last Updated: July 2025*
*System Version: Flask + PySpin + Systemd + Tailscale*
*Hardware: Raspberry Pi 4 + FLIR Blackfly S BFS-U3-200S6M*