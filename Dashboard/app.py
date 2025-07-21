# docker compose up --build -d dashboard
# xraypi:8080

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash
import os
import redis
import json
from datetime import datetime, timezone
from dotenv import load_dotenv
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
import logging
from flir import FlirCamera

# Load environment variables
load_dotenv('/app/config.env')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Initialize camera
camera = None
try:
    camera = FlirCamera()
    logger.info("Camera initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize camera: {e}")

# Database connections
redis_client = None
influx_client = None

def get_redis_connection():
    """Get Redis connection"""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'redis'),
                port=int(os.getenv('REDIS_PORT', '6379')),
                db=int(os.getenv('REDIS_DB', '0')),
                decode_responses=True
            )
            redis_client.ping()
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            redis_client = None
    return redis_client

def get_influx_connection():
    """Get InfluxDB connection"""
    global influx_client
    if influx_client is None:
        try:
            influx_client = InfluxDBClient(
                url=f"http://{os.getenv('INFLUXDB_HOST', 'influxdb')}:{os.getenv('INFLUXDB_PORT', '8086')}",
                token=os.getenv('INFLUXDB_TOKEN', ''),
                org=os.getenv('INFLUXDB_ORG', 'DAQ'),
                verify_ssl=False
            )
            # Test connection
            buckets_api = influx_client.buckets_api()
            buckets_api.find_buckets()
            logger.info("Connected to InfluxDB")
        except Exception as e:
            logger.error(f"InfluxDB connection failed: {e}")
            influx_client = None
    return influx_client

@app.route('/')
def home():
    """Services landing page - default page"""
    return render_template('landing.html')

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

@app.route('/redis')
def redis_demo():
    """Redis demo page"""
    redis_conn = get_redis_connection()
    
    # Get some sample data
    data = {}
    error = None
    
    if redis_conn:
        try:
            # Get all keys
            keys = redis_conn.keys('*') or []
            for key in keys[:10]:  # Limit to first 10 keys
                value = redis_conn.get(key)
                data[key] = value
        except Exception as e:
            error = f"Error reading from Redis: {e}"
    else:
        error = "Could not connect to Redis"
    
    return render_template('redis_demo.html', data=data, error=error)

@app.route('/redis/write', methods=['POST'])
def redis_write():
    """Write data to Redis"""
    redis_conn = get_redis_connection()
    
    if not redis_conn:
        flash('Could not connect to Redis', 'error')
        return redirect(url_for('redis_demo'))
    
    try:
        key = request.form.get('key', '').strip()
        value = request.form.get('value', '').strip()
        
        if not key:
            flash('Key cannot be empty', 'error')
            return redirect(url_for('redis_demo'))
        
        redis_conn.set(key, value)
        flash(f'Successfully set {key} = {value}', 'success')
    except Exception as e:
        flash(f'Error writing to Redis: {e}', 'error')
    
    return redirect(url_for('redis_demo'))

@app.route('/redis/delete', methods=['POST'])
def redis_delete():
    """Delete key from Redis"""
    redis_conn = get_redis_connection()
    
    if not redis_conn:
        flash('Could not connect to Redis', 'error')
        return redirect(url_for('redis_demo'))
    
    try:
        key = request.form.get('key', '').strip()
        if key and redis_conn.exists(key):
            redis_conn.delete(key)
            flash(f'Successfully deleted key: {key}', 'success')
        else:
            flash(f'Key not found: {key}', 'error')
    except Exception as e:
        flash(f'Error deleting from Redis: {e}', 'error')
    
    return redirect(url_for('redis_demo'))

@app.route('/influxdb')
def influxdb_demo():
    """InfluxDB demo page"""
    influx_conn = get_influx_connection()
    
    data = []
    error = None
    
    if influx_conn:
        try:
            # Query recent data
            bucket = os.getenv('INFLUXDB_BUCKET', 'logger')
            query = f'''
            from(bucket:"{bucket}")
            |> range(start: -1h)
            |> limit(n:10)
            '''
            
            query_api = influx_conn.query_api()
            result = query_api.query(query)
            
            for table in result:
                for record in table.records:
                    data.append({
                        'time': record.get_time().strftime('%Y-%m-%d %H:%M:%S'),
                        'measurement': record.get_measurement(),
                        'field': record.get_field(),
                        'value': record.get_value(),
                        'tags': record.values
                    })
        except Exception as e:
            error = f"Error reading from InfluxDB: {e}"
    else:
        error = "Could not connect to InfluxDB"
    
    return render_template('influxdb_demo.html', data=data, error=error)

@app.route('/influxdb/write', methods=['POST'])
def influxdb_write():
    """Write data to InfluxDB"""
    influx_conn = get_influx_connection()
    
    if not influx_conn:
        flash('Could not connect to InfluxDB', 'error')
        return redirect(url_for('influxdb_demo'))
    
    try:
        measurement = request.form.get('measurement', '').strip()
        field_name = request.form.get('field_name', '').strip()
        field_value = request.form.get('field_value', '').strip()
        tag_name = request.form.get('tag_name', '').strip()
        tag_value = request.form.get('tag_value', '').strip()
        
        if not all([measurement, field_name, field_value]):
            flash('Measurement, field name, and field value are required', 'error')
            return redirect(url_for('influxdb_demo'))
        
        # Convert field value to float
        try:
            field_value = float(field_value)
        except ValueError:
            flash('Field value must be a number', 'error')
            return redirect(url_for('influxdb_demo'))
        
        # Create point
        point = Point(measurement).field(field_name, field_value)
        
        # Add tag if provided
        if tag_name and tag_value:
            point = point.tag(tag_name, tag_value)
        
        # Add timestamp
        point = point.time(datetime.now(timezone.utc))
        
        # Write to InfluxDB
        bucket = os.getenv('INFLUXDB_BUCKET', 'logger')
        write_api = influx_conn.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket=bucket, record=point)
        
        flash(f'Successfully wrote point to {measurement}', 'success')
    except Exception as e:
        flash(f'Error writing to InfluxDB: {e}', 'error')
    
    return redirect(url_for('influxdb_demo'))

@app.route('/camera')
def camera_control():
    """Camera control page"""
    if not camera:
        flash('Camera not available', 'error')
        return redirect(url_for('home'))
    
    settings = camera.get_current_settings() if camera else None
    return render_template('camera_control.html', settings=settings)

@app.route('/camera/settings', methods=['POST'])
def update_camera_settings():
    """Update camera settings"""
    if not camera:
        return jsonify({'error': 'Camera not available'}), 503
    
    try:
        # Update gain
        if 'gain' in request.form:
            camera.set_gain(request.form['gain'])
        
        # Update exposure
        if 'exposure_time' in request.form:
            camera.set_exposure_time(request.form['exposure_time'])
        
        # Update ROI
        if all(k in request.form for k in ['width', 'height']):
            camera.set_roi(
                width=request.form['width'],
                height=request.form['height'],
                offset_x=request.form.get('offset_x', 0),
                offset_y=request.form.get('offset_y', 0)
            )
        
        # Get updated settings
        settings = camera.get_current_settings()
        flash('Camera settings updated successfully', 'success')
        return jsonify(settings)
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/camera/capture', methods=['POST'])
def capture_image():
    """Capture an image from the camera"""
    if not camera:
        return jsonify({'error': 'Camera not available'}), 503
    
    try:
        filename = camera.capture_image()
        if filename:
            return jsonify({
                'success': True,
                'filename': filename,
                'url': url_for('static', filename=f'captures/{filename}')
            })
        else:
            return jsonify({'error': 'Failed to capture image'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/health')
def health():
    """Health check endpoint"""
    redis_status = "connected" if get_redis_connection() else "disconnected"
    influx_status = "connected" if get_influx_connection() else "disconnected"
    
    return jsonify({
        'status': 'healthy', 
        'service': 'dashboard',
        'redis': redis_status,
        'influxdb': influx_status
    })

@app.route('/api/info')
def info():
    """Basic info endpoint"""
    return jsonify({
        'service': 'X-Ray Dashboard',
        'version': '2.0',
        'status': 'running',
        'features': ['redis_demo', 'influxdb_demo'],
        'environment': {
            'redis_host': os.getenv('REDIS_HOST', 'redis'),
            'influxdb_host': os.getenv('INFLUXDB_HOST', 'influxdb'),
            'influxdb_bucket': os.getenv('INFLUXDB_BUCKET', 'logger')
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True) 