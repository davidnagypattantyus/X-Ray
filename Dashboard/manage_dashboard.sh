#!/bin/bash

# X-Ray Dashboard Management Script
SERVICE_NAME="xray-dashboard.service"

case "$1" in
    start)
        echo "Starting X-Ray Dashboard..."
        sudo systemctl start $SERVICE_NAME
        ;;
    stop)
        echo "Stopping X-Ray Dashboard..."
        sudo systemctl stop $SERVICE_NAME
        ;;
    restart)
        echo "Restarting X-Ray Dashboard..."
        sudo systemctl restart $SERVICE_NAME
        ;;
    status)
        sudo systemctl status $SERVICE_NAME --no-pager -l
        ;;
    logs)
        echo "Recent logs for X-Ray Dashboard:"
        sudo journalctl -u $SERVICE_NAME -n 50 --no-pager
        ;;
    enable)
        echo "Enabling X-Ray Dashboard to start on boot..."
        sudo systemctl enable $SERVICE_NAME
        ;;
    disable)
        echo "Disabling X-Ray Dashboard auto-start..."
        sudo systemctl disable $SERVICE_NAME
        ;;
    *)
        echo "X-Ray Dashboard Management"
        echo "Usage: $0 {start|stop|restart|status|logs|enable|disable}"
        echo ""
        echo "Commands:"
        echo "  start    - Start the dashboard service"
        echo "  stop     - Stop the dashboard service"
        echo "  restart  - Restart the dashboard service"
        echo "  status   - Show service status"
        echo "  logs     - Show recent logs"
        echo "  enable   - Enable auto-start on boot"
        echo "  disable  - Disable auto-start on boot"
        echo ""
        echo "Website: http://192.168.99.110:8080"
        exit 1
        ;;
esac 