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
pip install flask opencv-python numpy scikit-image matplotlib

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
- **OpenCV**: Computer vision and image processing
- **NumPy**: Array operations (compatible version for PySpin)
- **scikit-image**: Advanced image processing algorithms
- **matplotlib**: Plotting and visualization

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

## 📊 **Complete Codebase Index & Technical Reference**

### 🏗️ **System Architecture Overview**

**Primary Deployment:** Systemd service (Flask + PySpin + OpenCV)  
**Alternative Deployment:** Docker Compose (legacy)  
**Network Access:** Local WiFi, Direct Ethernet (mDNS), Remote (Tailscale)  
**Total Codebase:** ~2,000 lines across core functionality

---

### 📂 **Core Application Files**

#### **`Dashboard/app.py`** (258 lines) - **Main Flask Application**
- **Framework:** Flask web server on port 8080
- **Camera Integration:** FLIR camera via `FlirLiveCamera` class
- **Control Integration:** X-ray tube control via `XRayControlLoop` class
- **Error Handling:** Graceful fallback when modules unavailable
- **Web Routes:**
  - `/` - Landing page with sci-fi theme
  - `/live-camera` - Camera control interface
  - `/control-loop` - X-ray tube control interface
- **API Endpoints:**
  - `/api/camera/status` - Camera availability and settings
  - `/api/camera/capture` - Manual image capture
  - `/api/camera/settings` - Update ISO/exposure
  - `/api/camera/image` - Get latest image (base64)
  - `/api/camera/save` - Save image to desktop
  - `/api/control-loop/status` - Control system status
  - `/api/control-loop/start|stop` - Control loop management
  - `/api/control-loop/parameters` - Update tube settings
  - `/api/control-loop/emergency-stop` - Safety shutdown

#### **`Dashboard/flir_live_simple.py`** (276 lines) - **FLIR Camera Interface**
- **Hardware:** FLIR Blackfly S BFS-U3-200S6M camera
- **SDK Integration:** PySpin with manual wheel installation
- **Image Processing:** OpenCV for all image operations (replaced Pillow)
- **Core Features:**
  - **1:1 Aspect Ratio:** 3648x3648 pixel capture for square display
  - **Manual Exposure:** Single-frame capture on demand
  - **ISO Control:** 100-6400 range (converted to camera gain)
  - **Exposure Control:** 10-5000ms range with microsecond precision
  - **Web Display:** Base64 JPEG encoding with OpenCV
  - **File Export:** Desktop JPEG save with timestamp
- **Technical Details:**
  - USB memory buffer: 256MB for high-speed USB 3.0
  - Image normalization: 8-bit conversion with proper scaling
  - Threading: Thread-safe image storage with locks
  - Error handling: Graceful camera initialization and cleanup

#### **`Dashboard/control_loop.py`** (176 lines) - **X-Ray Tube Control Simulation**
- **Threading:** Background control loop running at 10Hz
- **Control Parameters:**
  - **Input:** Tube current (0-500mA), Tube voltage (0-150kV)
  - **Output:** Filament current (A), Filament voltage (V)
- **Safety Features:**
  - Parameter limits and validation
  - Emergency stop functionality
  - Real-time status monitoring
- **Simulation Logic:**
  - Realistic tube/filament relationships
  - Random variation (±2% voltage, ±5% current)
  - Power calculation (P = V × I)

---

### 🌐 **Web Interface Templates**

#### **`Dashboard/templates/landing.html`** (155 lines) - **Main Entry Point**
- **Design Philosophy:** Sci-fi themed with professional aesthetics
- **Visual Elements:**
  - Animated shooting stars background
  - Glowing neon effects with CSS animations
  - Radiation and electrical danger symbols
- **Typography:** Orbitron font for futuristic appearance
- **Navigation:** Direct link to camera activation

#### **`Dashboard/templates/live_camera.html`** (521 lines) - **Camera Control Interface**
- **Design System:** Modern dark theme with DIN Sans typography
- **Layout Architecture:**
  - CSS Grid: 2fr 1fr split (image display + controls)
  - 1:1 aspect ratio image container
  - Responsive panel design
- **Interactive Features:**
  - **Real-time Status:** Camera initialization, resolution, current ISO
  - **Manual Capture:** "Take Exposure" button with feedback
  - **Dual Controls:** Sliders and number inputs (synchronized)
  - **Settings Management:** Live updates with validation
  - **Image Display:** Full-frame with timestamp overlay
  - **Save Functionality:** Desktop export with success/error messaging
- **JavaScript Functionality:**
  - 10-second status polling
  - Asynchronous API calls with error handling
  - Dynamic UI updates and form validation
  - Message system with auto-dismissal

#### **`Dashboard/templates/control_loop.html`** (486 lines) - **X-Ray Control Interface**
- **Design Consistency:** Matching dark theme with grid layouts
- **Panel Organization:**
  - **Control Panel:** Tube current/voltage inputs with validation
  - **Feedback Panel:** Real-time filament current/voltage displays
  - **Status Dashboard:** System state, power calculation, update timing
- **Control Features:**
  - Start/stop control loop management
  - Parameter updates with safety limits
  - Emergency stop with confirmation
  - Real-time power calculation display
- **Update System:**
  - 1-second refresh rate for real-time monitoring
  - Status indicators for system health
  - Error handling and user feedback

#### **`Dashboard/templates/index.html`** (170 lines) - **Legacy Dashboard**
- **Status:** Maintained for compatibility
- **Function:** Simple dashboard interface

---

### 🔧 **System Management & Configuration**

#### **`Dashboard/manage_dashboard.sh`** (50 lines) - **Service Control Script**
- **Available Commands:**
  - `start` - Start the dashboard service
  - `stop` - Stop the dashboard service  
  - `restart` - Restart the dashboard service
  - `status` - Show detailed service status
  - `logs` - Display recent service logs (50 lines)
  - `enable` - Enable auto-start on boot
  - `disable` - Disable auto-start on boot
- **Integration:** Direct systemd service management
- **Usage:** `./manage_dashboard.sh [command]`

#### **`/etc/systemd/system/xray-dashboard.service`** (22 lines) - **System Service Configuration**
- **Execution Context:**
  - User: `davidnagypattantyus` (non-root for security)
  - Groups: `plugdev`, `dialout` for USB device access
  - Working Directory: `/home/davidnagypattantyus/Desktop/repo/X-Ray/Dashboard`
- **Python Environment:** Virtual environment interpreter path
- **Service Management:**
  - Auto-restart on failure (RestartSec=10)
  - Boot integration (WantedBy=multi-user.target)
  - Journal logging integration
- **Network Dependencies:** Starts after network.target

---

### 📦 **Dependencies & Environment**

#### **`requirements.txt`** (13 lines) - **Python Dependencies**
```
flask>=2.3.0          # Web framework
werkzeug==3.0.1       # WSGI toolkit  
requests==2.31.0      # HTTP client library
numpy>=2.0.0          # Array operations
opencv-python>=4.8.0  # Computer vision and image processing
scikit-image>=0.21.0  # Advanced image processing algorithms
matplotlib>=3.7.0     # Plotting and visualization
# PySpin: Manually installed from wheel due to version compatibility
```

#### **`Dashboard/camera_env/`** - **Python Virtual Environment**
- **Python Version:** 3.11 (system Python)
- **PySpin Installation:** Manual wheel extraction and module renaming
- **Installation Process:**
  1. Extract wheel: `python -m zipfile -e spinnaker_python-*.whl temp_wheel/`
  2. Copy modules: `cp -r temp_wheel/PySpin* camera_env/lib/python3.11/site-packages/`
  3. Rename dist-info for Python 3.11 compatibility
- **Location:** `/home/davidnagypattantyus/Desktop/repo/X-Ray/Dashboard/camera_env/`

#### **Spinnaker SDK Files:**
- **`spinnaker-4.2.0.88-arm64-22.04-pkg.tar`** (47MB) - Main SDK for ARM64
- **`spinnaker_python-4.2.0.88-cp310-cp310-linux_aarch64.whl`** (9.8MB) - Python bindings

---

### 🌐 **Network Architecture & Access**

#### **Access Methods:**
1. **Local Network WiFi/Ethernet:** `http://192.168.x.x:8080`
   - Dynamic IP assignment via DHCP
   - Full functionality on local network
   
2. **Direct Ethernet Connection:** `http://xraypi.local:8080`
   - mDNS hostname resolution via Avahi
   - Auto-negotiated link-local addressing
   - No internet required
   
3. **Remote Access:** `http://100.109.159.37:8080`
   - Tailscale VPN with static IP
   - Encrypted tunnel access from anywhere
   - Cross-platform compatibility

#### **Network Services:**
- **Avahi Daemon:** mDNS/Bonjour hostname broadcasting
- **Tailscale:** Mesh VPN for remote access
- **Flask Development Server:** Debug mode, all interfaces (0.0.0.0:8080)

---

### 🔄 **Alternative Deployment: Docker**

#### **`compose.yml`** (30 lines) - **Docker Compose Configuration**
- **Status:** Legacy/alternative deployment method
- **Service Configuration:**
  - Single dashboard container
  - USB device and volume mapping for camera access
  - Port mapping: 80 (differs from systemd: 8080)
  - Health checks and restart policies
- **Usage:** `docker compose up --build -d`

#### **Docker Benefits:**
- Isolated environment
- Easy deployment across systems
- Consistent dependency management
- Container orchestration capabilities

---

### 🎯 **Feature Matrix & Capabilities**

#### **Camera Control Features:**
- ✅ **FLIR Integration:** Full PySpin SDK integration
- ✅ **Manual Exposure:** Single-frame capture on demand
- ✅ **Real-time Controls:** ISO (100-6400), Exposure (10-5000ms)
- ✅ **Settings Synchronization:** Sliders ↔ Input boxes
- ✅ **1:1 Display:** Square aspect ratio (3648x3648)
- ✅ **Image Export:** Desktop JPEG save with timestamps
- ✅ **Status Monitoring:** Camera health and configuration
- ✅ **Error Handling:** Graceful failure and recovery

#### **X-Ray Simulation Features:**
- ✅ **Tube Control:** Current (0-500mA), Voltage (0-150kV)
- ✅ **Filament Feedback:** Simulated current/voltage responses
- ✅ **Safety Systems:** Parameter limits and emergency stop
- ✅ **Real-time Monitoring:** 1Hz status updates
- ✅ **Power Calculation:** Real-time wattage display
- ✅ **Threading:** Non-blocking background control loop

#### **Web Interface Features:**
- ✅ **Modern Design:** Dark theme with professional aesthetics
- ✅ **Responsive Layout:** CSS Grid and Flexbox
- ✅ **Typography:** DIN Sans and monospace fonts
- ✅ **Interactive Controls:** Real-time updates and validation
- ✅ **Message System:** Success/error notifications
- ✅ **Navigation:** Seamless page transitions

#### **System Integration Features:**
- ✅ **Auto-boot:** Systemd service with dependency management
- ✅ **Multi-access:** Local, direct, and remote connectivity
- ✅ **Error Recovery:** Service restart and graceful degradation
- ✅ **Logging:** Centralized journal integration
- ✅ **Security:** Non-root execution with minimal privileges

---

### 🚀 **Advanced Processing Readiness**

#### **OpenCV Foundation for Future Features:**
The migration from Pillow to OpenCV provides a solid foundation for advanced X-ray image processing:

- **Dark Frame Correction:** `cv2.subtract()` for background removal
- **Flat Field Correction:** `cv2.divide()` for illumination normalization  
- **Noise Reduction:** `cv2.fastNlMeansDenoising()` for image cleanup
- **Histogram Enhancement:** `cv2.equalizeHist()`, `cv2.createCLAHE()`
- **Multi-frame Processing:** `cv2.addWeighted()` for averaging
- **Image Alignment:** `cv2.findTransformECC()` for registration
- **ROI Analysis:** Built-in statistical functions
- **False Color Mapping:** `cv2.applyColorMap()` for visualization

#### **Planned Advanced Workflow:**
```
Raw Capture → Dark Correction → Light Correction → Processing → Web Display
     ↓              ↓               ↓              ↓           ↓
  PySpin         OpenCV          OpenCV        OpenCV    OpenCV/Web
```

#### **Future Enhancement Areas:**
- **Multi-exposure HDR processing**
- **Real-time image enhancement pipelines**
- **Advanced ROI analysis and measurements**
- **Metadata export with DICOM compatibility**
- **GPU acceleration for real-time processing**

---

### 🔍 **Troubleshooting Quick Reference**

#### **Common Issues & Solutions:**

**Camera Not Detected:**
```bash
# Check USB connection
lsusb | grep -i "1e10\|Point Grey"

# Reload udev rules
sudo udevadm control --reload-rules && sudo udevadm trigger

# Restart service
sudo systemctl restart xray-dashboard.service
```

**Service Issues:**
```bash
# Check service status
systemctl status xray-dashboard.service

# View live logs
journalctl -u xray-dashboard.service -f

# Test Python environment
/home/davidnagypattantyus/Desktop/repo/X-Ray/Dashboard/camera_env/bin/python -c "import cv2, PySpin; print('All modules OK')"
```

**Network Access Issues:**
```bash
# Test local access
curl -s http://localhost:8080/api/camera/status

# Check Tailscale
tailscale status

# Test mDNS resolution
avahi-resolve-host-name xraypi.local
```

---

### 📈 **Performance Specifications**

#### **System Performance:**
- **Boot Time:** ~30 seconds to full dashboard availability
- **Camera Initialization:** ~2-3 seconds after USB detection
- **Image Capture:** ~500ms for full 3648x3648 resolution
- **Control Loop Frequency:** 10Hz background operation
- **Web Interface Updates:** 1-10 second refresh rates
- **Memory Usage:** ~150MB for Flask app + camera drivers
- **Network Latency:** <100ms on local network, varies on Tailscale

#### **Image Processing:**
- **Resolution:** 3648x3648 pixels (1:1 aspect ratio)
- **Bit Depth:** 8-bit normalized from camera raw data
- **Format:** JPEG with configurable quality (85% web, 95% export)
- **Encoding:** Base64 for web display, direct file for export
- **Processing Time:** <100ms for conversion and encoding

---

### 🛡️ **Security & Deployment Considerations**

#### **Security Features:**
- **Non-root Execution:** Service runs as regular user
- **Minimal Privileges:** Limited to USB device access groups
- **Local Network Only:** Flask debug mode not internet-exposed
- **VPN Access:** Encrypted Tailscale tunnel for remote access
- **USB Permissions:** Restricted to plugdev group members

#### **Production Considerations:**
- **Debug Mode:** Currently enabled - disable for production
- **HTTPS:** Consider SSL/TLS for sensitive deployments
- **Authentication:** No authentication currently implemented
- **Firewall:** Configure iptables for additional security
- **Logging:** Monitor journal logs for security events

---

*Last Updated: July 2025*  
*System Version: Flask + PySpin + Systemd + Tailscale + OpenCV*  
*Hardware: Raspberry Pi 4 + FLIR Blackfly S BFS-U3-200S6M*  
*Codebase: ~2,000 lines across core functionality*