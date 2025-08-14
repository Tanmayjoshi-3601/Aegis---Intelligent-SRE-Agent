#!/bin/bash

# SRE Kafka Streaming Pipeline Cleanup Script
# Stops all services, removes containers, volumes, and resets everything

set -e

# Colors and emojis
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

SUCCESS="✅"
ERROR="❌"
WARNING="⚠️"
INFO="ℹ️"
CLEANUP="🧹"
STOP="⏹️"
REMOVE="🗑️"
RESET="🔄"

echo -e "${BLUE}${CLEANUP} SRE Kafka Streaming Pipeline Cleanup${NC}"
echo "=============================================="

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

# Function to stop all services
stop_services() {
    print_status "info" "Stopping all Docker services..."
    
    if command_exists docker-compose; then
        docker-compose down --remove-orphans 2>/dev/null || true
        print_status "success" "Docker Compose services stopped"
    else
        print_status "warning" "docker-compose not found, stopping containers manually..."
        
        # Stop containers manually
        containers=("sre-zookeeper" "sre-kafka" "sre-redis" "sre-postgres" "sre-rabbitmq" "sre-kafka-ui" "sre-qdrant")
        
        for container in "${containers[@]}"; do
            if docker ps --format "{{.Names}}" | grep -q "^$container$"; then
                print_status "info" "Stopping container: $container"
                docker stop "$container" 2>/dev/null || true
                print_status "success" "Container $container stopped"
            else
                print_status "info" "Container $container not running"
            fi
        done
    fi
}

# Function to remove containers
remove_containers() {
    print_status "info" "Removing containers..."
    
    containers=("sre-zookeeper" "sre-kafka" "sre-redis" "sre-postgres" "sre-rabbitmq" "sre-kafka-ui" "sre-qdrant" "sre-dev-runner")
    
    for container in "${containers[@]}"; do
        if docker ps -a --format "{{.Names}}" | grep -q "^$container$"; then
            print_status "info" "Removing container: $container"
            docker rm -f "$container" 2>/dev/null || true
            print_status "success" "Container $container removed"
        else
            print_status "info" "Container $container not found"
        fi
    done
}

# Function to remove volumes
remove_volumes() {
    print_status "info" "Removing volumes..."
    
    volumes=("sre-kafka-streaming_redis-data" "sre-kafka-streaming_postgres-data" "sre-kafka-streaming_rabbitmq-data" "sre-kafka-streaming_qdrant-data")
    
    for volume in "${volumes[@]}"; do
        if docker volume ls --format "{{.Name}}" | grep -q "^$volume$"; then
            print_status "info" "Removing volume: $volume"
            docker volume rm "$volume" 2>/dev/null || true
            print_status "success" "Volume $volume removed"
        else
            print_status "info" "Volume $volume not found"
        fi
    done
    
    # Also try with default naming
    default_volumes=("redis-data" "postgres-data" "rabbitmq-data" "qdrant-data")
    
    for volume in "${default_volumes[@]}"; do
        if docker volume ls --format "{{.Name}}" | grep -q "^$volume$"; then
            print_status "info" "Removing volume: $volume"
            docker volume rm "$volume" 2>/dev/null || true
            print_status "success" "Volume $volume removed"
        fi
    done
}

# Function to remove networks
remove_networks() {
    print_status "info" "Removing networks..."
    
    networks=("sre-kafka-streaming_sre-network" "sre-network")
    
    for network in "${networks[@]}"; do
        if docker network ls --format "{{.Name}}" | grep -q "^$network$"; then
            print_status "info" "Removing network: $network"
            docker network rm "$network" 2>/dev/null || true
            print_status "success" "Network $network removed"
        else
            print_status "info" "Network $network not found"
        fi
    done
}

# Function to remove temporary files
remove_temp_files() {
    print_status "info" "Removing temporary files..."
    
    temp_files=("/tmp/sre_producer.sh" "/tmp/sre_consumer.sh" "/tmp/sre_monitor.sh")
    
    for file in "${temp_files[@]}"; do
        if [ -f "$file" ]; then
            print_status "info" "Removing temporary file: $file"
            rm -f "$file"
            print_status "success" "Temporary file $file removed"
        else
            print_status "info" "Temporary file $file not found"
        fi
    done
}

# Function to clean up Python cache files
cleanup_python_cache() {
    print_status "info" "Cleaning up Python cache files..."
    
    # Remove __pycache__ directories
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    print_status "success" "Python cache directories removed"
    
    # Remove .pyc files
    find . -name "*.pyc" -delete 2>/dev/null || true
    print_status "success" "Python compiled files removed"
    
    # Remove .pyo files
    find . -name "*.pyo" -delete 2>/dev/null || true
    print_status "success" "Python optimized files removed"
}

# Function to reset Kafka topics
reset_kafka_topics() {
    print_status "info" "Resetting Kafka topics..."
    
    # Check if Kafka is still running
    if nc -z localhost 9092 2>/dev/null; then
        print_status "info" "Kafka is still running, attempting to delete topics..."
        
        # Delete system-logs topic
        docker exec sre-kafka kafka-topics \
            --delete \
            --topic system-logs \
            --bootstrap-server localhost:9092 2>/dev/null || {
            print_status "warning" "Failed to delete system-logs topic (may not exist)"
        }
        
        # Delete other potential topics
        topics=("test-topic" "logs" "events" "metrics")
        for topic in "${topics[@]}"; do
            docker exec sre-kafka kafka-topics \
                --delete \
                --topic "$topic" \
                --bootstrap-server localhost:9092 2>/dev/null || {
                print_status "info" "Topic $topic not found or already deleted"
            }
        done
        
        print_status "success" "Kafka topics reset"
    else
        print_status "info" "Kafka not running, skipping topic deletion"
    fi
}

# Function to clean up consumer groups
cleanup_consumer_groups() {
    print_status "info" "Cleaning up consumer groups..."
    
    # Check if Kafka is still running
    if nc -z localhost 9092 2>/dev/null; then
        consumer_groups=("sre-agent-consumer" "test-consumer-group" "sre-monitor-group")
        
        for group in "${consumer_groups[@]}"; do
            print_status "info" "Resetting consumer group: $group"
            docker exec sre-kafka kafka-consumer-groups \
                --bootstrap-server localhost:9092 \
                --group "$group" \
                --reset-offsets \
                --to-earliest \
                --execute \
                --all-topics 2>/dev/null || {
                print_status "warning" "Failed to reset consumer group $group (may not exist)"
            }
        done
        
        print_status "success" "Consumer groups reset"
    else
        print_status "info" "Kafka not running, skipping consumer group cleanup"
    fi
}

# Function to show cleanup summary
show_cleanup_summary() {
    echo ""
    echo -e "${CYAN}${CLEANUP} CLEANUP SUMMARY${NC}"
    echo "=================="
    
    # Check what's still running
    echo -e "${BLUE}${INFO} Checking remaining containers:${NC}"
    remaining_containers=$(docker ps -a --format "{{.Names}}" | grep -E "(sre-|kafka|zookeeper|redis|postgres|rabbitmq)" || true)
    
    if [ -n "$remaining_containers" ]; then
        echo -e "${YELLOW}${WARNING} Remaining containers:${NC}"
        echo "$remaining_containers"
    else
        echo -e "${GREEN}${SUCCESS} No remaining containers${NC}"
    fi
    
    # Check remaining volumes
    echo -e "${BLUE}${INFO} Checking remaining volumes:${NC}"
    remaining_volumes=$(docker volume ls --format "{{.Name}}" | grep -E "(redis|postgres|rabbitmq|qdrant)" || true)
    
    if [ -n "$remaining_volumes" ]; then
        echo -e "${YELLOW}${WARNING} Remaining volumes:${NC}"
        echo "$remaining_volumes"
    else
        echo -e "${GREEN}${SUCCESS} No remaining volumes${NC}"
    fi
    
    # Check remaining networks
    echo -e "${BLUE}${INFO} Checking remaining networks:${NC}"
    remaining_networks=$(docker network ls --format "{{.Name}}" | grep -E "(sre|kafka)" || true)
    
    if [ -n "$remaining_networks" ]; then
        echo -e "${YELLOW}${WARNING} Remaining networks:${NC}"
        echo "$remaining_networks"
    else
        echo -e "${GREEN}${SUCCESS} No remaining networks${NC}"
    fi
    
    # Check if ports are still in use
    echo -e "${BLUE}${INFO} Checking if ports are still in use:${NC}"
    ports=("9092" "2181" "6379" "5432" "5672" "8080")
    services=("Kafka" "Zookeeper" "Redis" "PostgreSQL" "RabbitMQ" "Kafka UI")
    
    for i in "${!ports[@]}"; do
        if nc -z localhost "${ports[$i]}" 2>/dev/null; then
            echo -e "${YELLOW}${WARNING} Port ${ports[$i]} (${services[$i]}) is still in use${NC}"
        else
            echo -e "${GREEN}${SUCCESS} Port ${ports[$i]} (${services[$i]}) is free${NC}"
        fi
    done
}

# Function to perform full cleanup
full_cleanup() {
    print_status "info" "Starting full cleanup process..."
    
    # Stop services first
    stop_services
    
    # Wait a moment for services to stop
    sleep 2
    
    # Remove containers
    remove_containers
    
    # Remove volumes
    remove_volumes
    
    # Remove networks
    remove_networks
    
    # Remove temporary files
    remove_temp_files
    
    # Clean up Python cache
    cleanup_python_cache
    
    # Reset Kafka topics (if possible)
    reset_kafka_topics
    
    # Clean up consumer groups (if possible)
    cleanup_consumer_groups
    
    print_status "success" "Full cleanup completed!"
}

# Function to perform soft cleanup (keep data)
soft_cleanup() {
    print_status "info" "Starting soft cleanup (keeping data)..."
    
    # Stop services
    stop_services
    
    # Wait a moment for services to stop
    sleep 2
    
    # Remove containers (but keep volumes)
    remove_containers
    
    # Remove networks
    remove_networks
    
    # Remove temporary files
    remove_temp_files
    
    # Clean up Python cache
    cleanup_python_cache
    
    print_status "success" "Soft cleanup completed! (Data volumes preserved)"
}

# Function to show menu
show_menu() {
    echo -e "${CYAN}${CLEANUP} Cleanup Options${NC}"
    echo "==============="
    echo "1. Stop services only"
    echo "2. Soft cleanup (keep data)"
    echo "3. Full cleanup (remove everything)"
    echo "4. Remove containers only"
    echo "5. Remove volumes only"
    echo "6. Remove networks only"
    echo "7. Clean temporary files"
    echo "8. Reset Kafka topics"
    echo "9. Show cleanup summary"
    echo "0. Exit"
    echo ""
}

# Main execution
main() {
    # Check if Docker is available
    if ! command_exists docker; then
        print_status "error" "Docker is not installed or not available"
        exit 1
    fi
    
    # Check if script is run with arguments
    if [ $# -eq 0 ]; then
        while true; do
            show_menu
            read -p "Select an option (0-9): " choice
            
            case $choice in
                1) stop_services ;;
                2) soft_cleanup ;;
                3) full_cleanup ;;
                4) remove_containers ;;
                5) remove_volumes ;;
                6) remove_networks ;;
                7) remove_temp_files; cleanup_python_cache ;;
                8) reset_kafka_topics; cleanup_consumer_groups ;;
                9) show_cleanup_summary ;;
                0) 
                    print_status "success" "Exiting cleanup script"
                    exit 0
                    ;;
                *)
                    print_status "error" "Invalid option. Please select 0-9."
                    ;;
            esac
            
            echo ""
            read -p "Press Enter to continue..."
            echo ""
        done
    else
        case $1 in
            "stop") stop_services ;;
            "soft") soft_cleanup ;;
            "full") full_cleanup ;;
            "containers") remove_containers ;;
            "volumes") remove_volumes ;;
            "networks") remove_networks ;;
            "temp") remove_temp_files; cleanup_python_cache ;;
            "topics") reset_kafka_topics; cleanup_consumer_groups ;;
            "summary") show_cleanup_summary ;;
            *)
                print_status "error" "Unknown command: $1"
                echo "Available commands: stop, soft, full, containers, volumes, networks, temp, topics, summary"
                exit 1
                ;;
        esac
    fi
}

# Run main function
main "$@" 