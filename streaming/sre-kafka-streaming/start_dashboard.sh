#!/bin/bash

# SRE Agent Dashboard Startup Script
# This script starts the SRE Agent Dashboard server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DASHBOARD_PORT=8081
DASHBOARD_HOST="0.0.0.0"
PID_FILE="dashboard.pid"
LOG_FILE="dashboard.log"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if port is available
check_port() {
    if lsof -Pi :$DASHBOARD_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_error "Port $DASHBOARD_PORT is already in use"
        exit 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    print_status "Python version: $PYTHON_VERSION"
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed"
        exit 1
    fi
    
    # Check if frontend directory exists
    if [ ! -d "frontend" ]; then
        print_error "Frontend directory not found"
        exit 1
    fi
    
    # Check if dashboard server file exists
    if [ ! -f "dashboard_server.py" ]; then
        print_error "dashboard_server.py not found"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dashboard dependencies..."
    
    if [ -f "requirements-dashboard.txt" ]; then
        pip3 install -r requirements-dashboard.txt
        print_success "Dependencies installed"
    else
        print_warning "requirements-dashboard.txt not found, installing basic Flask dependencies"
        pip3 install Flask Flask-CORS
        print_success "Basic dependencies installed"
    fi
}

# Function to start dashboard
start_dashboard() {
    print_status "Starting SRE Agent Dashboard..."
    
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            print_warning "Dashboard is already running (PID: $PID)"
            return
        else
            print_warning "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi
    
    # Check port availability
    check_port
    
    # Start the dashboard server
    nohup python3 dashboard_server.py > "$LOG_FILE" 2>&1 &
    DASHBOARD_PID=$!
    
    # Save PID
    echo $DASHBOARD_PID > "$PID_FILE"
    
    # Wait a moment for server to start
    sleep 2
    
    # Check if server started successfully
    if ps -p $DASHBOARD_PID > /dev/null 2>&1; then
        print_success "Dashboard started successfully (PID: $DASHBOARD_PID)"
        print_status "Dashboard URL: http://localhost:$DASHBOARD_PORT"
        print_status "API Base URL: http://localhost:$DASHBOARD_PORT/api"
        print_status "Log file: $LOG_FILE"
    else
        print_error "Failed to start dashboard"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# Function to stop dashboard
stop_dashboard() {
    print_status "Stopping SRE Agent Dashboard..."
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID
            rm -f "$PID_FILE"
            print_success "Dashboard stopped"
        else
            print_warning "Dashboard is not running"
            rm -f "$PID_FILE"
        fi
    else
        print_warning "No PID file found"
    fi
}

# Function to restart dashboard
restart_dashboard() {
    print_status "Restarting SRE Agent Dashboard..."
    stop_dashboard
    sleep 2
    start_dashboard
}

# Function to check dashboard status
check_status() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null 2>&1; then
            print_success "Dashboard is running (PID: $PID)"
            print_status "Dashboard URL: http://localhost:$DASHBOARD_PORT"
            
            # Check if server is responding
            if curl -s http://localhost:$DASHBOARD_PORT/api/health > /dev/null 2>&1; then
                print_success "Dashboard is responding to health checks"
            else
                print_warning "Dashboard is running but not responding to health checks"
            fi
        else
            print_error "Dashboard is not running (stale PID file)"
            rm -f "$PID_FILE"
        fi
    else
        print_warning "Dashboard is not running (no PID file)"
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        print_status "Showing dashboard logs (last 50 lines):"
        tail -n 50 "$LOG_FILE"
    else
        print_warning "No log file found"
    fi
}

# Function to show help
show_help() {
    echo "SRE Agent Dashboard Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the dashboard server"
    echo "  stop      Stop the dashboard server"
    echo "  restart   Restart the dashboard server"
    echo "  status    Check dashboard status"
    echo "  logs      Show dashboard logs"
    echo "  install   Install dependencies"
    echo "  check     Check prerequisites"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start      # Start the dashboard"
    echo "  $0 status     # Check if dashboard is running"
    echo "  $0 logs       # View dashboard logs"
}

# Main script logic
case "${1:-start}" in
    start)
        check_prerequisites
        install_dependencies
        start_dashboard
        ;;
    stop)
        stop_dashboard
        ;;
    restart)
        check_prerequisites
        restart_dashboard
        ;;
    status)
        check_status
        ;;
    logs)
        show_logs
        ;;
    install)
        install_dependencies
        ;;
    check)
        check_prerequisites
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac 