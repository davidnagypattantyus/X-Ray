# 🎯 X-Ray Dashboard Demo Usage Guide

## Getting Started

1. **Start the system:**
   ```bash
   cp config.env.example config.env
   docker compose up --build -d
   ```

2. **Access the Dashboard:**
   Open http://localhost:8080

## 🗄️ Redis Demo Usage

### Writing Data
1. Navigate to http://localhost:8080/redis
2. **Custom Key-Value:**
   - Enter key: `user:123:name`
   - Enter value: `John Doe`
   - Click "Set Key-Value"

3. **Quick Actions:**
   - Click "Set Current Timestamp" to add a timestamp
   - Click "Initialize Counter" to create a counter
   - Click "Set Status Online" to set system status

### Reading Data
- View the "Current Redis Data" table
- See all keys and their values
- Monitor connection status

### Deleting Data
- Click the "Delete" button next to any key
- Confirm deletion in the popup

## 📈 InfluxDB Demo Usage

### Writing Time-Series Data
1. Navigate to http://localhost:8080/influxdb
2. **Custom Data Point:**
   - Measurement: `temperature`
   - Field Name: `celsius`
   - Field Value: `23.5`
   - Tag Name: `location`
   - Tag Value: `lab1`
   - Click "Write Point"

3. **Quick Sample Data:**
   - Click "Add Temperature Reading" for sample temp data
   - Click "Add Humidity Reading" for sample humidity data
   - Click "Add Counter Point" for sample counter data

### Reading Time-Series Data
- View the "Recent InfluxDB Data" table
- See timestamps, measurements, fields, values, and tags
- Data automatically refreshes every 60 seconds

## 🔧 Health Monitoring

### Dashboard Health Check
- Visit http://localhost:8080/health
- JSON response shows:
  ```json
  {
    "status": "healthy",
    "service": "dashboard", 
    "redis": "connected",
    "influxdb": "connected"
  }
  ```

### System Information
- Visit http://localhost:8080/api/info
- JSON response shows service details and environment

## 📊 Integration with Other Services

### Grafana Visualization
1. Access Grafana: http://localhost:3000 (admin/admin)
2. Add InfluxDB as data source:
   - URL: `http://influxdb:8086`
   - Organization: `DAQ`
   - Token: `(from config.env)`
   - Bucket: `logger`
3. Create dashboards to visualize your demo data

### Portainer Management
1. Access Portainer: http://localhost:9000
2. Monitor container health and logs
3. View resource usage

## 🎮 Sample Demo Workflow

### Scenario: Temperature Monitoring System

1. **Setup Data:**
   ```
   Go to /influxdb
   Add Temperature Reading (22.5°C, lab1)
   Add Temperature Reading (23.1°C, lab1) 
   Add Temperature Reading (21.8°C, lab2)
   ```

2. **Add Metadata to Redis:**
   ```
   Go to /redis
   Set: sensor:lab1:type = "DS18B20"
   Set: sensor:lab1:location = "Main Lab"
   Set: sensor:lab2:type = "DHT22"
   Set: alert:threshold = "25.0"
   ```

3. **Monitor Data:**
   - Check InfluxDB demo page for time-series data
   - Check Redis demo page for metadata
   - View both in near real-time with auto-refresh

4. **Visualize in Grafana:**
   - Create temperature trend graphs
   - Set up alerts for threshold values
   - Build dashboards combining both data sources

## 🔄 Advanced Usage

### Custom Measurements
- **IoT Sensors**: `measurement=iot_sensor, field=value, tags=device_id,type`
- **System Metrics**: `measurement=system, field=cpu_usage, tags=server,environment`
- **Business Data**: `measurement=sales, field=amount, tags=region,product`

### Redis Patterns
- **Session Storage**: `session:{user_id}:{data}`
- **Configuration**: `config:{service}:{setting}`
- **Counters**: `counter:{metric}:{period}`
- **Caching**: `cache:{key}:{timestamp}`

This enhanced dashboard provides a complete testing and monitoring environment for your X-Ray DAQ system! 🚀 