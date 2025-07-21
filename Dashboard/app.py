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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True) 