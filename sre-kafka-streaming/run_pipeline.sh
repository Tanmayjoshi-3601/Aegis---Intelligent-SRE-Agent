#!/bin/bash

# SRE Kafka Streaming Pipeline Setup Script
# This script sets up the entire pipeline with proper error handling and status indicators

set -e  # Exit on any error

# Colors and emojis for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Emojis
SUCCESS="✅"
ERROR="❌"
WARNING="⚠️"
INFO="ℹ️"
ROCKET="🚀"
GEAR="⚙️"
HEALTH="🏥"
TOPIC="📝"
NETWORK="🌐"

echo -e "${BLUE}${ROCKET} SRE Kafka Streaming Pipeline Setup${NC}"
echo "=================================================="

# Function to print status messages
print_status() {
    local status=$1
    local message=$2
    case $status in
        "success")
            echo -e "${GREEN}${SUCCESS} $message${NC}"
            ;;
        "error")
            echo -e "${RED}${ERROR} $message${NC}"
            ;;
        "warning")
            echo -e "${YELLOW}${WARNING} $message${NC}"
            ;;
        "info")
            echo -e "${BLUE}${INFO} $message${NC}"
            ;;
    esac
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to wait for service health
wait_for_service() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    print_status "info" "Waiting for $service to be healthy on port $port..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z localhost $port 2>/dev/null; then
            print_status "success" "$service is healthy and ready!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_status "error" "$service failed to become healthy after $max_attempts attempts"
    return 1
}

# Check if Docker is installed and running
print_status "info" "Checking Docker installation and status..."

if ! command_exists docker; then
    print_status "error" "Docker is not installed. Please install Docker Desktop first."
    exit 1
fi

if ! docker info >/dev/null 2>&1; then
    print_status "error" "Docker is not running. Please start Docker Desktop."
    exit 1
fi

print_status "success" "Docker is running"

# Check if docker-compose is available
if ! command_exists docker-compose; then
    print_status "error" "docker-compose is not installed. Please install docker-compose."
    exit 1
fi

print_status "success" "docker-compose is available"

# Stop any existing containers
print_status "info" "Stopping any existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true
print_status "success" "Existing containers stopped"

# Start all services
print_status "info" "Starting all Docker services..."
docker-compose up -d

# Wait for services to be healthy
print_status "info" "Waiting for services to become healthy..."

# Wait for Zookeeper
wait_for_service "Zookeeper" 2181

# Wait for Kafka
wait_for_service "Kafka" 9092

# Wait for Redis
wait_for_service "Redis" 6379

# Wait for PostgreSQL
wait_for_service "PostgreSQL" 5432

# Wait for RabbitMQ
wait_for_service "RabbitMQ" 5672

# Wait for Kafka UI
wait_for_service "Kafka UI" 8080

print_status "success" "All services are healthy and ready!"

# Create Kafka topic
print_status "info" "Creating Kafka topic 'system-logs'..."

# Wait a bit more for Kafka to be fully ready
sleep 10

# Create topic with proper configuration
docker exec sre-kafka kafka-topics \
    --create \
    --if-not-exists \
    --bootstrap-server localhost:9092 \
    --replication-factor 1 \
    --partitions 3 \
    --topic system-logs \
    --config retention.ms=86400000 \
    --config cleanup.policy=delete \
    --config max.message.bytes=1048576

if [ $? -eq 0 ]; then
    print_status "success" "Kafka topic 'system-logs' created successfully"
else
    print_status "warning" "Topic creation failed, but it might already exist"
fi

# Verify topic creation
print_status "info" "Verifying topic creation..."
docker exec sre-kafka kafka-topics \
    --list \
    --bootstrap-server localhost:9092 | grep system-logs

if [ $? -eq 0 ]; then
    print_status "success" "Topic verification successful"
else
    print_status "error" "Topic verification failed"
    exit 1
fi

# Test Kafka connectivity
print_status "info" "Testing Kafka connectivity..."

# Test producer
echo '{"test": "message"}' | docker exec -i sre-kafka kafka-console-producer \
    --bootstrap-server localhost:9092 \
    --topic system-logs

if [ $? -eq 0 ]; then
    print_status "success" "Kafka producer test successful"
else
    print_status "error" "Kafka producer test failed"
    exit 1
fi

# Test consumer (with timeout)
timeout 10s docker exec sre-kafka kafka-console-consumer \
    --bootstrap-server localhost:9092 \
    --topic system-logs \
    --from-beginning \
    --max-messages 1 > /dev/null 2>&1

if [ $? -eq 0 ] || [ $? -eq 124 ]; then  # 124 is timeout exit code
    print_status "success" "Kafka consumer test successful"
else
    print_status "error" "Kafka consumer test failed"
    exit 1
fi

# Check service status
print_status "info" "Checking service status..."

echo ""
echo -e "${BLUE}${HEALTH} Service Status:${NC}"
echo "=================="

# Check all containers are running
for service in zookeeper kafka redis postgres rabbitmq kafka-ui; do
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "sre-$service.*Up"; then
        echo -e "${GREEN}${SUCCESS} sre-$service: Running${NC}"
    else
        echo -e "${RED}${ERROR} sre-$service: Not running${NC}"
    fi
done

# Display connection information
echo ""
echo -e "${BLUE}${NETWORK} Connection Information:${NC}"
echo "=========================="
echo "Kafka: localhost:9092"
echo "Kafka UI: http://localhost:8080"
echo "Zookeeper: localhost:2181"
echo "Redis: localhost:6379"
echo "PostgreSQL: localhost:5432"
echo "RabbitMQ: localhost:5672"
echo "RabbitMQ Management: http://localhost:15672"

# Check if Python dependencies are available
print_status "info" "Checking Python dependencies..."

if command_exists python3; then
    # Check if kafka-python is available
    if python3 -c "import kafka" 2>/dev/null; then
        print_status "success" "Python Kafka library is available"
    else
        print_status "warning" "Python Kafka library not found. Run: pip install kafka-python"
    fi
else
    print_status "warning" "Python3 not found. Please install Python 3.8+"
fi

# Final success message
echo ""
echo -e "${GREEN}${ROCKET} Pipeline Setup Complete!${NC}"
echo "=================================="
echo -e "${GREEN}${SUCCESS} All services are running and healthy${NC}"
echo -e "${GREEN}${SUCCESS} Kafka topic 'system-logs' is ready${NC}"
echo -e "${GREEN}${SUCCESS} You can now run the streaming pipeline${NC}"
echo ""
echo "Next steps:"
echo "1. Run: ./test_streaming.py"
echo "2. Run: ./start_streaming.sh"
echo "3. Run: ./monitor.py"
echo ""
echo -e "${BLUE}${INFO} To stop all services: docker-compose down${NC}"
echo -e "${BLUE}${INFO} To view logs: docker-compose logs -f [service-name]${NC}" 