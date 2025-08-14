#!/bin/bash

# SRE Agent System Startup Script
# ===============================
# This script starts the Intelligent SRE Agent system with proper setup and monitoring.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="config/sre_agent_config.json"
LOG_DIR="logs"
DATA_DIR="data"
PID_FILE="logs/sre_agent.pid"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Function to check if process is running
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            rm -f "$PID_FILE"
        fi
    fi
    return 1
}

# Function to stop the SRE agent
stop_agent() {
    print_status "Stopping SRE Agent..."
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            print_status "Sending SIGTERM to process $pid..."
            kill -TERM "$pid"
            
            # Wait for graceful shutdown
            local count=0
            while ps -p "$pid" > /dev/null 2>&1 && [ $count -lt 30 ]; do
                sleep 1
                count=$((count + 1))
            done
            
            if ps -p "$pid" > /dev/null 2>&1; then
                print_warning "Process did not stop gracefully, sending SIGKILL..."
                kill -KILL "$pid"
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    print_status "SRE Agent stopped."
}

# Function to check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi
    
    local python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_status "Python version: $python_version"
    
    # Check if required packages are installed
    local required_packages=("kafka-python" "asyncio" "sqlite3")
    for package in "${required_packages[@]}"; do
        if ! python3 -c "import $package" 2>/dev/null; then
            print_warning "Package $package not found. Installing..."
            pip3 install "$package"
        fi
    done
    
    # Check if Kafka is running (optional)
    if command -v docker &> /dev/null; then
        if docker ps | grep -q kafka; then
            print_status "Kafka is running in Docker."
        else
            print_warning "Kafka not detected. Make sure Kafka is running before starting the agent."
        fi
    else
        print_warning "Docker not found. Make sure Kafka is running before starting the agent."
    fi
    
    # Create necessary directories
    mkdir -p "$LOG_DIR" "$DATA_DIR" "data/knowledge_base"
    print_status "Directories created."
}

# Function to validate configuration
validate_config() {
    print_header "Validating Configuration..."
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file $CONFIG_FILE not found."
        exit 1
    fi
    
    if ! python3 -c "import json; json.load(open('$CONFIG_FILE'))" 2>/dev/null; then
        print_error "Invalid JSON in configuration file $CONFIG_FILE."
        exit 1
    fi
    
    print_status "Configuration validated."
}

# Function to start the SRE agent
start_agent() {
    print_header "Starting SRE Agent System..."
    
    if is_running; then
        print_warning "SRE Agent is already running."
        return 0
    fi
    
    # Start the agent in background
    print_status "Starting Kafka SRE integration..."
    nohup python3 kafka_sre_integration.py > "$LOG_DIR/sre_agent.out" 2>&1 &
    local pid=$!
    
    # Save PID
    echo "$pid" > "$PID_FILE"
    
    # Wait a moment to check if it started successfully
    sleep 2
    
    if ps -p "$pid" > /dev/null 2>&1; then
        print_status "SRE Agent started successfully with PID $pid"
        print_status "Logs are being written to $LOG_DIR/sre_agent.log"
        print_status "Output is being written to $LOG_DIR/sre_agent.out"
        return 0
    else
        print_error "Failed to start SRE Agent. Check logs for details."
        rm -f "$PID_FILE"
        return 1
    fi
}

# Function to show status
show_status() {
    print_header "SRE Agent Status"
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_status "SRE Agent is running (PID: $pid)"
        
        # Show recent logs
        if [ -f "$LOG_DIR/sre_agent.log" ]; then
            echo ""
            print_status "Recent logs:"
            tail -10 "$LOG_DIR/sre_agent.log"
        fi
    else
        print_warning "SRE Agent is not running."
    fi
}

# Function to show logs
show_logs() {
    if [ -f "$LOG_DIR/sre_agent.log" ]; then
        print_header "SRE Agent Logs"
        tail -f "$LOG_DIR/sre_agent.log"
    else
        print_warning "No log file found."
    fi
}

# Function to run tests
run_tests() {
    print_header "Running SRE Agent System Tests..."
    
    if [ -f "test_sre_agent_system.py" ]; then
        python3 test_sre_agent_system.py
    else
        print_error "Test file test_sre_agent_system.py not found."
        exit 1
    fi
}

# Function to show help
show_help() {
    echo "SRE Agent System Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the SRE Agent system"
    echo "  stop      Stop the SRE Agent system"
    echo "  restart   Restart the SRE Agent system"
    echo "  status    Show the status of the SRE Agent"
    echo "  logs      Show live logs"
    echo "  test      Run the test suite"
    echo "  check     Check prerequisites and configuration"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start    # Start the system"
    echo "  $0 status   # Check if it's running"
    echo "  $0 logs     # View live logs"
    echo "  $0 stop     # Stop the system"
}

# Main script logic
case "${1:-help}" in
    start)
        check_prerequisites
        validate_config
        start_agent
        ;;
    stop)
        stop_agent
        ;;
    restart)
        stop_agent
        sleep 2
        check_prerequisites
        validate_config
        start_agent
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    test)
        run_tests
        ;;
    check)
        check_prerequisites
        validate_config
        print_status "All checks passed!"
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