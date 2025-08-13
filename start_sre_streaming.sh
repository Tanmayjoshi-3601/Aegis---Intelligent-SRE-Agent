#!/bin/bash

# SRE Application - Kafka Streaming Startup Script
# ================================================
# This script starts the complete SRE streaming pipeline including:
# - Kafka infrastructure (Zookeeper + Kafka)
# - SRE application streaming service
# - Real-time monitoring and analysis

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
KAFKA_DIR="$(pwd)/sre-kafka-streaming"
SRE_APP_DIR="$(pwd)"
DOCKER_COMPOSE_FILE="$KAFKA_DIR/docker-compose.yml"
STREAMING_SCRIPT="$(pwd)/streaming_integration.py"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker Desktop first."
        exit 1
    fi
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is not installed or not in PATH"
        exit 1
    fi
    
    # Check if required files exist
    if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
        error "Docker compose file not found: $DOCKER_COMPOSE_FILE"
        exit 1
    fi
    
    if [ ! -f "$STREAMING_SCRIPT" ]; then
        error "Streaming script not found: $STREAMING_SCRIPT"
        exit 1
    fi
    
    log "✅ Prerequisites check passed"
}

# Start Kafka infrastructure
start_kafka() {
    log "Starting Kafka infrastructure..."
    
    # Start Zookeeper and Kafka
    log "Starting Zookeeper and Kafka containers..."
    (cd "$KAFKA_DIR" && docker-compose up -d zookeeper kafka)
    
    # Wait for Kafka to be ready
    log "Waiting for Kafka to be ready..."
    sleep 15
    
    # Create Kafka topic
    log "Creating Kafka topic..."
    docker exec sre-kafka kafka-topics \
        --bootstrap-server localhost:9092 \
        --create \
        --topic system-logs \
        --partitions 3 \
        --replication-factor 1 \
        --if-not-exists 2>/dev/null || true
    
    # Verify topic creation
    log "Verifying Kafka topic..."
    docker exec sre-kafka kafka-topics \
        --bootstrap-server localhost:9092 \
        --list | grep system-logs || {
        error "Failed to create Kafka topic"
        exit 1
    }
    
    log "✅ Kafka infrastructure started successfully"
}

# Check if Kafka is running
check_kafka_running() {
    log "Checking if Kafka is running..."
    
    # Try to connect to Kafka
    python3 -c "
import sys
sys.path.append('$KAFKA_DIR')
try:
    from kafka import KafkaProducer
    producer = KafkaProducer(bootstrap_servers='localhost:9093')
    producer.close()
    print('Kafka is running')
except Exception as e:
    print(f'Kafka connection failed: {e}')
    sys.exit(1)
" 2>/dev/null || {
        error "Kafka is not running or not accessible"
        return 1
    }
    
    log "✅ Kafka is running and accessible"
    return 0
}

# Start the SRE streaming service
start_sre_streaming() {
    log "Starting SRE streaming service..."
    
    # Check if logs exist
    if [ ! -f "data/synthetic/streaming/logs.json" ]; then
        error "Streaming logs not found. Please generate logs first."
        exit 1
    fi
    
    if [ ! -f "data/synthetic/streaming/metadata.json" ]; then
        error "Streaming metadata not found. Please generate logs first."
        exit 1
    fi
    
    # Start the streaming service
    log "Starting streaming service with real-time analysis..."
    python3 "$STREAMING_SCRIPT" \
        --mode normal \
        --rate 10 \
        --kafka-servers localhost:9093 \
        --topic system-logs
}

# Start monitoring (optional)
start_monitoring() {
    log "Starting monitoring service..."
    
    # Start the monitoring script in background
    (cd "$KAFKA_DIR" && python3 monitor.py) &
    MONITOR_PID=$!
    
    log "✅ Monitoring started (PID: $MONITOR_PID)"
    echo $MONITOR_PID > .monitor.pid
}

# Cleanup function
cleanup() {
    log "Cleaning up..."
    
    # Stop monitoring if running
    if [ -f .monitor.pid ]; then
        MONITOR_PID=$(cat .monitor.pid)
        if kill -0 $MONITOR_PID 2>/dev/null; then
            log "Stopping monitoring service..."
            kill $MONITOR_PID
        fi
        rm -f .monitor.pid
    fi
    
    # Stop Kafka infrastructure
    log "Stopping Kafka infrastructure..."
    (cd "$KAFKA_DIR" && docker-compose down)
    
    log "✅ Cleanup completed"
}

# Show status
show_status() {
    log "Current status:"
    
    # Check Docker containers
    echo "Docker containers:"
    (cd "$KAFKA_DIR" && docker-compose ps)
    
    # Check Kafka topic
    echo -e "\nKafka topics:"
    docker exec sre-kafka kafka-topics --bootstrap-server localhost:9092 --list 2>/dev/null || echo "Kafka not accessible"
    
    # Check if monitoring is running
    if [ -f .monitor.pid ]; then
        MONITOR_PID=$(cat .monitor.pid)
        if kill -0 $MONITOR_PID 2>/dev/null; then
            echo -e "\nMonitoring service: Running (PID: $MONITOR_PID)"
        else
            echo -e "\nMonitoring service: Not running"
            rm -f .monitor.pid
        fi
    else
        echo -e "\nMonitoring service: Not running"
    fi
}

# Main function
main() {
    case "${1:-start}" in
        "start")
            log "🚀 Starting SRE Kafka Streaming Pipeline"
            check_prerequisites
            start_kafka
            sleep 5
            check_kafka_running
            start_monitoring
            start_sre_streaming
            ;;
        "stop")
            log "🛑 Stopping SRE Kafka Streaming Pipeline"
            cleanup
            ;;
        "restart")
            log "🔄 Restarting SRE Kafka Streaming Pipeline"
            cleanup
            sleep 2
            check_prerequisites
            start_kafka
            sleep 5
            check_kafka_running
            start_monitoring
            start_sre_streaming
            ;;
        "status")
            show_status
            ;;
        "kafka-only")
            log "📊 Starting Kafka infrastructure only"
            check_prerequisites
            start_kafka
            check_kafka_running
            ;;
        "streaming-only")
            log "📡 Starting streaming service only"
            check_kafka_running || exit 1
            start_sre_streaming
            ;;
        "help"|"-h"|"--help")
            echo "SRE Kafka Streaming Pipeline"
            echo ""
            echo "Usage: $0 [command]"
            echo ""
            echo "Commands:"
            echo "  start         Start the complete pipeline (default)"
            echo "  stop          Stop all services"
            echo "  restart       Restart all services"
            echo "  status        Show current status"
            echo "  kafka-only    Start only Kafka infrastructure"
            echo "  streaming-only Start only streaming service"
            echo "  help          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 start              # Start complete pipeline"
            echo "  $0 --rate 20          # Start with 20 logs/sec"
            echo "  $0 --mode burst       # Start in burst mode"
            echo "  $0 --duration 30      # Run for 30 minutes"
            ;;
        *)
            error "Unknown command: $1"
            echo "Use '$0 help' for usage information"
            exit 1
            ;;
    esac
}

# Handle command line arguments for streaming
STREAMING_ARGS=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --rate)
            STREAMING_ARGS="$STREAMING_ARGS --rate $2"
            shift 2
            ;;
        --mode)
            STREAMING_ARGS="$STREAMING_ARGS --mode $2"
            shift 2
            ;;
        --duration)
            STREAMING_ARGS="$STREAMING_ARGS --duration $2"
            shift 2
            ;;
        --kafka-servers)
            STREAMING_ARGS="$STREAMING_ARGS --kafka-servers $2"
            shift 2
            ;;
        --topic)
            STREAMING_ARGS="$STREAMING_ARGS --topic $2"
            shift 2
            ;;
        --no-ml)
            STREAMING_ARGS="$STREAMING_ARGS --no-ml"
            shift
            ;;
        *)
            break
            ;;
    esac
done

# Set up signal handlers
trap cleanup EXIT
trap 'log "Interrupted by user"; exit 1' INT TERM

# Run main function
main "$@"
