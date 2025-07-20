# 🔍 X-Ray DAQ System

A simplified Data Acquisition (DAQ) system with Flask dashboard, Redis messaging, InfluxDB storage, and monitoring services.

## 🚀 Quick Start

1. **Copy the configuration file:**
   ```bash
   cp config.env.example config.env
   ```

2. **Build and start all services:**
   ```bash
   docker compose up --build -d
   ```

3. **Access the services:**
   - **Dashboard**: http://localhost:8080 (Enhanced Flask app with database demos)
     - **Redis Demo**: http://localhost:8080/redis
     - **InfluxDB Demo**: http://localhost:8080/influxdb
   - **Grafana**: http://localhost:3000 (admin/admin)
   - **InfluxDB**: http://localhost:8086
   - **Portainer**: http://localhost:9000
   - **UI**: http://localhost:8081
   - **Redis**: localhost:6379

## 📁 Project Structure

```
X-Ray/
├── compose.yml              # Docker Compose configuration
├── requirements.txt         # Master Python dependencies
├── config.env.example      # Environment variables template
├── test_setup.py           # Setup verification script
├── Dashboard/              # Simple Flask hello world app
│   ├── app.py             
│   ├── Dockerfile.Dashboard
│   └── templates/index.html
├── Logger/                 # Data logger service
│   ├── async_logger.py
│   ├── daq_core.py        # Configuration module
│   └── Dockerfile.Logger
└── UI/                     # NiceGUI user interface
    ├── UI.py
    ├── redis_client.py     # Redis pub/sub handler
    ├── components.py       # UI components
    └── Dockerfile.UI
```

## 🛠️ Services

- **Dashboard**: Enhanced Flask application with Redis & InfluxDB demo pages
  - Redis Demo: Read/write key-value data with interactive forms
  - InfluxDB Demo: Time-series data operations with real-time display
  - Health monitoring and system information
- **Logger**: Async data logger with Redis and InfluxDB integration
- **UI**: NiceGUI-based user interface with Redis messaging
- **Redis**: Message broker and caching
- **InfluxDB**: Time-series database
- **Grafana**: Data visualization and dashboards
- **Portainer**: Docker container management

## 🔧 Configuration

All services use a single `requirements.txt` file with compatible package versions:
- Flask ≥2.3.0 for web framework
- Redis ≥5.0.0 for messaging
- InfluxDB client ≥1.36.0 for database
- NiceGUI ≥1.4.0 for modern UI
- Aiohttp ≥3.8.0 for async networking

## 🧪 Testing

Run the verification script to check your setup:
```bash
python test_setup.py
```

## 📝 Notes

- **Enhanced Dashboard**: Now includes interactive Redis and InfluxDB demo pages
- **Database Integration**: Full read/write functionality for both databases
- **Single Requirements**: All services use one master `requirements.txt` file
- **Simplified Dockerfiles**: Consistent patterns across all services
- **Proper Networking**: All services can communicate with each other
- **Health Monitoring**: Health checks configured for all services
- **Error Handling**: Graceful degradation when databases are unavailable

## 🎯 Dashboard Features

### Redis Demo (`/redis`)
- **Write Operations**: Set key-value pairs with custom or quick-action buttons
- **Read Operations**: View all stored keys and their values in a table
- **Delete Operations**: Remove individual keys with confirmation
- **Connection Status**: Real-time Redis connection monitoring
- **Auto-refresh**: Page refreshes every 30 seconds

### InfluxDB Demo (`/influxdb`)
- **Write Time-Series Data**: Add measurements with fields and tags
- **Sample Data**: Quick buttons for temperature, humidity, and counter data
- **Read Recent Data**: View last hour's data in a formatted table
- **Query Results**: Display measurements, fields, values, and tags
- **Connection Status**: Real-time InfluxDB connection monitoring
- **Auto-refresh**: Page refreshes every 60 seconds

## 🔄 Development

To modify services:
1. Edit the service code
2. Rebuild: `docker compose up --build -d [service-name]`
3. Check logs: `docker compose logs [service-name]`

Enjoy your simplified X-Ray DAQ system! 🎉