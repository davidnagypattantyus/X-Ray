# FLIR Camera Dashboard
# Standalone camera interface

from flask import Flask, render_template, jsonify, request, flash, redirect, url_for
import os
import json
from datetime import datetime
import logging

# Optional FLIR camera import
try:
    from flir_live_simple import FlirLiveCamera
    FLIR_AVAILABLE = True
except ImportError as e:
    print(f"FLIR camera not available: {e}")
    FlirLiveCamera = None
    FLIR_AVAILABLE = False

# Optional Control Loop import
try:
    from control_loop import XRayControlLoop
    CONTROL_LOOP_AVAILABLE = True
except ImportError as e:
    print(f"Control loop not available: {e}")
    XRayControlLoop = None
    CONTROL_LOOP_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'camera-dashboard-secret-key'

# Initialize camera
live_camera = None
if FLIR_AVAILABLE:
    try:
        live_camera = FlirLiveCamera()
        logger.info("Camera initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize camera: {e}")
else:
    logger.info("FLIR camera not available - running without camera support")

# Initialize control loop
control_loop = None
if CONTROL_LOOP_AVAILABLE:
    try:
        control_loop = XRayControlLoop()
        control_loop.start_control_loop()
        logger.info("Control loop initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize control loop: {e}")
else:
    logger.info("Control loop not available - running without control loop support")

@app.route('/')
def home():
    """Landing page with navigation to camera"""
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    """Original dashboard page"""
    return render_template('index.html')

@app.route('/landing')
def landing():
    """Services landing page (alias for root)"""
    return render_template('landing.html')

@app.route('/xray-image')
def xray_image():
    """X-Ray image display page"""
    return render_template('xray_image.html')

@app.route('/live-camera')
def live_camera_page():
    """Live camera page"""
    settings = {}
    if live_camera:
        settings = live_camera.get_settings()
    return render_template('live_camera.html', settings=settings)

@app.route('/api/camera/image')
def get_camera_image():
    """API endpoint to get the latest camera image"""
    if not live_camera:
        return jsonify({'error': 'Camera not available'}), 503
    
    image_data = live_camera.get_latest_image()
    if image_data:
        return jsonify({
            'success': True,
            'image': image_data,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({'error': 'No image available'}), 404

@app.route('/api/camera/histogram')
def get_camera_histogram():
    """API endpoint to get the latest image histogram"""
    if not live_camera:
        return jsonify({'error': 'Camera not available'}), 503
    
    histogram_data = live_camera.get_latest_histogram()
    if histogram_data:
        return jsonify({
            'success': True,
            'histogram': histogram_data,
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({'error': 'No histogram available'}), 404

@app.route('/api/camera/save', methods=['POST'])
def save_camera_image():
    """API endpoint to save the current image to desktop"""
    if not live_camera:
        return jsonify({'error': 'Camera not available'}), 503
    
    filename = live_camera.save_current_image()
    if filename:
        return jsonify({
            'success': True,
            'filename': filename,
            'message': f'Image saved as {filename}'
        })
    else:
        return jsonify({'error': 'Failed to save image'}), 400

@app.route('/api/camera/capture', methods=['POST'])
def capture_manual_image():
    """API endpoint to manually capture an image"""
    if not live_camera:
        return jsonify({'error': 'Camera not available'}), 503
    
    try:
        success = live_camera.capture_single_image()
        if success:
            return jsonify({
                'success': True,
                'message': 'Image captured successfully',
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to capture image'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/camera/settings', methods=['POST'])
def update_camera_settings():
    """API endpoint to update camera settings"""
    if not live_camera:
        return jsonify({'error': 'Camera not available'}), 503
    
    try:
        data = request.get_json()
        
        if 'exposure' in data:
            live_camera.set_exposure(data['exposure'])
        
        if 'iso' in data:
            live_camera.set_iso(data['iso'])
        elif 'gain' in data:
            live_camera.set_gain(data['gain'])
        
        # Get updated settings
        settings = live_camera.get_settings()
        return jsonify({
            'success': True,
            'settings': settings
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/camera/status')
def camera_status():
    """API endpoint to get camera status"""
    if not live_camera:
        return jsonify({'available': False, 'initialized': False})
    
    return jsonify({
        'available': True,
        'initialized': live_camera.is_initialized,
        'settings': live_camera.get_settings()
    })

@app.route('/control-loop')
def control_loop_page():
    """X-Ray tube control loop page"""
    return render_template('control_loop.html')

# Control Loop API endpoints
@app.route('/api/control-loop/status')
def control_loop_status():
    """API endpoint to get control loop status"""
    if not control_loop:
        return jsonify({'success': False, 'error': 'Control loop not available'})
    
    try:
        parameters = control_loop.get_all_parameters()
        return jsonify({
            'success': True,
            'parameters': parameters
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/control-loop/start', methods=['POST'])
def start_control_loop():
    """API endpoint to start control loop"""
    if not control_loop:
        return jsonify({'success': False, 'error': 'Control loop not available'})
    
    try:
        success = control_loop.start_control_loop()
        if success:
            return jsonify({'success': True, 'message': 'Control loop started'})
        else:
            return jsonify({'success': False, 'error': 'Failed to start control loop'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/control-loop/stop', methods=['POST'])
def stop_control_loop():
    """API endpoint to stop control loop"""
    if not control_loop:
        return jsonify({'success': False, 'error': 'Control loop not available'})
    
    try:
        control_loop.stop_control_loop()
        return jsonify({'success': True, 'message': 'Control loop stopped'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/control-loop/parameters', methods=['POST'])
def update_control_parameters():
    """API endpoint to update control parameters"""
    if not control_loop:
        return jsonify({'success': False, 'error': 'Control loop not available'})
    
    try:
        data = request.get_json()
        tube_current = data.get('tube_current', 0)
        tube_voltage = data.get('tube_voltage', 0)
        
        success = control_loop.set_tube_parameters(tube_current, tube_voltage)
        if success:
            return jsonify({'success': True, 'message': 'Parameters updated'})
        else:
            return jsonify({'success': False, 'error': 'Failed to update parameters'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/control-loop/emergency-stop', methods=['POST'])
def emergency_stop_control_loop():
    """API endpoint for emergency stop"""
    if not control_loop:
        return jsonify({'success': False, 'error': 'Control loop not available'})
    
    try:
        success = control_loop.emergency_stop()
        if success:
            return jsonify({'success': True, 'message': 'Emergency stop activated'})
        else:
            return jsonify({'success': False, 'error': 'Emergency stop failed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True) 