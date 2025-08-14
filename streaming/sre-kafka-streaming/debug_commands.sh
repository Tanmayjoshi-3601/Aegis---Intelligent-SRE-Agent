#!/bin/bash

# SRE Kafka Streaming Pipeline Debug Commands
# Collection of useful commands for troubleshooting and debugging

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
DEBUG="🔍"
NETWORK="🌐"
TOPIC="📝"
CONSUMER="📥"
PRODUCER="📤"
LAG="⏱️"

echo -e "${BLUE}${DEBUG} SRE Kafka Streaming Pipeline Debug Commands${NC}"
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

# Function to check if Docker containers are running
check_docker_containers() {
    echo -e "${CYAN}${DEBUG} Checking Docker Container Status${NC}"
    echo "=================================="
    
    containers=("sre-zookeeper" "sre-kafka" "sre-redis" "sre-postgres" "sre-rabbitmq" "sre-kafka-ui")
    
    for container in "${containers[@]}"; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container.*Up"; then
            echo -e "${GREEN}${SUCCESS} $container: Running${NC}"
        else
            echo -e "${RED}${ERROR} $container: Not running${NC}"
        fi
    done
    echo ""
}

# Function to check Kafka connectivity
check_kafka_connectivity() {
    echo -e "${CYAN}${NETWORK} Checking Kafka Connectivity${NC}"
    echo "============================="
    
    # Check if Kafka is listening on port 9092
    if nc -z localhost 9092 2>/dev/null; then
        print_status "success" "Kafka is listening on localhost:9092"
    else
        print_status "error" "Kafka is not listening on localhost:9092"
        return 1
    fi
    
    # Check if Zookeeper is listening on port 2181
    if nc -z localhost 2181 2>/dev/null; then
        print_status "success" "Zookeeper is listening on localhost:2181"
    else
        print_status "error" "Zookeeper is not listening on localhost:2181"
    fi
    
    # Test Kafka broker API versions
    echo -e "${BLUE}${INFO} Testing Kafka broker API versions...${NC}"
    docker exec sre-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 2>/dev/null || {
        print_status "error" "Failed to connect to Kafka broker"
        return 1
    }
    print_status "success" "Kafka broker API test successful"
    echo ""
}

# Function to list Kafka topics
list_kafka_topics() {
    echo -e "${CYAN}${TOPIC} Listing Kafka Topics${NC}"
    echo "====================="
    
    echo -e "${BLUE}${INFO} Available topics:${NC}"
    docker exec sre-kafka kafka-topics \
        --list \
        --bootstrap-server localhost:9092 2>/dev/null || {
        print_status "error" "Failed to list Kafka topics"
        return 1
    }
    echo ""
    
    # Show detailed topic information
    echo -e "${BLUE}${INFO} Detailed topic information:${NC}"
    docker exec sre-kafka kafka-topics \
        --describe \
        --bootstrap-server localhost:9092 2>/dev/null || {
        print_status "error" "Failed to describe Kafka topics"
        return 1
    }
    echo ""
}

# Function to check consumer groups
check_consumer_groups() {
    echo -e "${CYAN}${CONSUMER} Checking Consumer Groups${NC}"
    echo "========================="
    
    echo -e "${BLUE}${INFO} Active consumer groups:${NC}"
    docker exec sre-kafka kafka-consumer-groups \
        --list \
        --bootstrap-server localhost:9092 2>/dev/null || {
        print_status "error" "Failed to list consumer groups"
        return 1
    }
    echo ""
    
    # Check lag for specific consumer groups
    consumer_groups=("sre-agent-consumer" "test-consumer-group" "sre-monitor-group")
    
    for group in "${consumer_groups[@]}"; do
        echo -e "${BLUE}${INFO} Consumer group lag for '$group':${NC}"
        docker exec sre-kafka kafka-consumer-groups \
            --describe \
            --group "$group" \
            --bootstrap-server localhost:9092 2>/dev/null || {
            print_status "warning" "Consumer group '$group' not found or no activity"
        }
        echo ""
    done
}

# Function to view recent messages in topic
view_recent_messages() {
    echo -e "${CYAN}${PRODUCER} Viewing Recent Messages in system-logs Topic${NC}"
    echo "==============================================="
    
    echo -e "${BLUE}${INFO} Fetching last 5 messages from system-logs topic...${NC}"
    echo -e "${YELLOW}${WARNING} Press Ctrl+C to stop${NC}"
    echo ""
    
    docker exec sre-kafka kafka-console-consumer \
        --bootstrap-server localhost:9092 \
        --topic system-logs \
        --from-beginning \
        --max-messages 5 \
        --property print.timestamp=true \
        --property print.key=true \
        --property print.value=true 2>/dev/null || {
        print_status "error" "Failed to consume messages from system-logs topic"
        return 1
    }
    echo ""
}

# Function to check topic offsets
check_topic_offsets() {
    echo -e "${CYAN}${LAG} Checking Topic Offsets${NC}"
    echo "======================="
    
    echo -e "${BLUE}${INFO} Current offsets for system-logs topic:${NC}"
    docker exec sre-kafka kafka-run-class kafka.tools.GetOffsetShell \
        --bootstrap-server localhost:9092 \
        --topic system-logs \
        --time -1 2>/dev/null || {
        print_status "error" "Failed to get topic offsets"
        return 1
    }
    echo ""
    
    echo -e "${BLUE}${INFO} Earliest offsets for system-logs topic:${NC}"
    docker exec sre-kafka kafka-run-class kafka.tools.GetOffsetShell \
        --bootstrap-server localhost:9092 \
        --topic system-logs \
        --time -2 2>/dev/null || {
        print_status "error" "Failed to get earliest offsets"
        return 1
    }
    echo ""
}

# Function to check Kafka logs
check_kafka_logs() {
    echo -e "${CYAN}${DEBUG} Checking Kafka Logs${NC}"
    echo "====================="
    
    echo -e "${BLUE}${INFO} Recent Kafka broker logs:${NC}"
    docker logs --tail 20 sre-kafka 2>/dev/null || {
        print_status "error" "Failed to get Kafka logs"
        return 1
    }
    echo ""
    
    echo -e "${BLUE}${INFO} Recent Zookeeper logs:${NC}"
    docker logs --tail 10 sre-zookeeper 2>/dev/null || {
        print_status "error" "Failed to get Zookeeper logs"
        return 1
    }
    echo ""
}

# Function to check network connectivity
check_network_connectivity() {
    echo -e "${CYAN}${NETWORK} Checking Network Connectivity${NC}"
    echo "==============================="
    
    local ports=("9092" "2181" "6379" "5432" "5672" "8080")
    local services=("Kafka" "Zookeeper" "Redis" "PostgreSQL" "RabbitMQ" "Kafka UI")
    
    for i in "${!ports[@]}"; do
        if nc -z localhost "${ports[$i]}" 2>/dev/null; then
            print_status "success" "${services[$i]} is accessible on port ${ports[$i]}"
        else
            print_status "error" "${services[$i]} is not accessible on port ${ports[$i]}"
        fi
    done
    echo ""
}

# Function to check Python dependencies
check_python_dependencies() {
    echo -e "${CYAN}${DEBUG} Checking Python Dependencies${NC}"
    echo "============================="
    
    if command_exists python3; then
        print_status "success" "Python3 is available"
        
        # Check kafka-python
        if python3 -c "import kafka" 2>/dev/null; then
            print_status "success" "kafka-python library is available"
        else
            print_status "error" "kafka-python library is not available"
            print_status "info" "Install with: pip install kafka-python"
        fi
        
        # Check other common dependencies
        local deps=("json" "time" "datetime" "logging" "threading" "signal")
        for dep in "${deps[@]}"; do
            if python3 -c "import $dep" 2>/dev/null; then
                print_status "success" "Python module '$dep' is available"
            else
                print_status "error" "Python module '$dep' is not available"
            fi
        done
    else
        print_status "error" "Python3 is not available"
    fi
    echo ""
}

# Function to test producer connectivity
test_producer_connectivity() {
    echo -e "${CYAN}${PRODUCER} Testing Producer Connectivity${NC}"
    echo "==============================="
    
    echo -e "${BLUE}${INFO} Sending test message to system-logs topic...${NC}"
    
    # Create a test message
    test_message='{"test": "debug_message", "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'", "service": "debug-service"}'
    
    echo "$test_message" | docker exec -i sre-kafka kafka-console-producer \
        --bootstrap-server localhost:9092 \
        --topic system-logs 2>/dev/null
    
    if [ $? -eq 0 ]; then
        print_status "success" "Test message sent successfully"
    else
        print_status "error" "Failed to send test message"
        return 1
    fi
    echo ""
}

# Function to check Kafka configuration
check_kafka_config() {
    echo -e "${CYAN}${DEBUG} Checking Kafka Configuration${NC}"
    echo "==============================="
    
    echo -e "${BLUE}${INFO} Kafka broker configuration:${NC}"
    docker exec sre-kafka kafka-configs \
        --bootstrap-server localhost:9092 \
        --entity-type brokers \
        --entity-name 1 \
        --describe 2>/dev/null || {
        print_status "error" "Failed to get Kafka configuration"
        return 1
    }
    echo ""
}

# Function to check topic configuration
check_topic_config() {
    echo -e "${CYAN}${TOPIC} Checking Topic Configuration${NC}"
    echo "==============================="
    
    echo -e "${BLUE}${INFO} system-logs topic configuration:${NC}"
    docker exec sre-kafka kafka-configs \
        --bootstrap-server localhost:9092 \
        --entity-type topics \
        --entity-name system-logs \
        --describe 2>/dev/null || {
        print_status "warning" "Topic configuration not found or topic doesn't exist"
        return 1
    }
    echo ""
}

# Function to show troubleshooting tips
show_troubleshooting_tips() {
    echo -e "${CYAN}${DEBUG} Troubleshooting Tips${NC}"
    echo "====================="
    echo ""
    echo -e "${YELLOW}${WARNING} Common Issues and Solutions:${NC}"
    echo ""
    echo "1. ${BLUE}Kafka not accessible:${NC}"
    echo "   - Check if Docker containers are running: docker ps"
    echo "   - Restart services: docker-compose restart"
    echo "   - Check Docker logs: docker logs sre-kafka"
    echo ""
    echo "2. ${BLUE}Topic not found:${NC}"
    echo "   - Create topic: docker exec sre-kafka kafka-topics --create --topic system-logs --bootstrap-server localhost:9092"
    echo "   - Check topic list: docker exec sre-kafka kafka-topics --list --bootstrap-server localhost:9092"
    echo ""
    echo "3. ${BLUE}Consumer group issues:${NC}"
    echo "   - Reset consumer group: docker exec sre-kafka kafka-consumer-groups --bootstrap-server localhost:9092 --group [group-name] --reset-offsets --to-earliest --execute"
    echo "   - Check consumer lag: docker exec sre-kafka kafka-consumer-groups --bootstrap-server localhost:9092 --group [group-name] --describe"
    echo ""
    echo "4. ${BLUE}Python connection issues:${NC}"
    echo "   - Check if kafka-python is installed: pip install kafka-python"
    echo "   - Verify bootstrap servers: localhost:9092"
    echo "   - Check firewall settings"
    echo ""
    echo "5. ${BLUE}Performance issues:${NC}"
    echo "   - Check system resources: docker stats"
    echo "   - Monitor Kafka metrics: http://localhost:8080"
    echo "   - Check topic partitions and replication"
    echo ""
}

# Main menu function
show_menu() {
    echo -e "${CYAN}${DEBUG} Debug Commands Menu${NC}"
    echo "=================="
    echo "1. Check Docker containers"
    echo "2. Check Kafka connectivity"
    echo "3. List Kafka topics"
    echo "4. Check consumer groups"
    echo "5. View recent messages"
    echo "6. Check topic offsets"
    echo "7. Check Kafka logs"
    echo "8. Check network connectivity"
    echo "9. Check Python dependencies"
    echo "10. Test producer connectivity"
    echo "11. Check Kafka configuration"
    echo "12. Check topic configuration"
    echo "13. Show troubleshooting tips"
    echo "14. Run all checks"
    echo "0. Exit"
    echo ""
}

# Function to run all checks
run_all_checks() {
    echo -e "${BLUE}${INFO} Running all diagnostic checks...${NC}"
    echo ""
    
    check_docker_containers
    check_kafka_connectivity
    list_kafka_topics
    check_consumer_groups
    check_topic_offsets
    check_kafka_logs
    check_network_connectivity
    check_python_dependencies
    test_producer_connectivity
    check_kafka_config
    check_topic_config
    
    echo -e "${GREEN}${SUCCESS} All diagnostic checks completed!${NC}"
    echo ""
}

# Main execution
main() {
    while true; do
        show_menu
        read -p "Select an option (0-14): " choice
        
        case $choice in
            1) check_docker_containers ;;
            2) check_kafka_connectivity ;;
            3) list_kafka_topics ;;
            4) check_consumer_groups ;;
            5) view_recent_messages ;;
            6) check_topic_offsets ;;
            7) check_kafka_logs ;;
            8) check_network_connectivity ;;
            9) check_python_dependencies ;;
            10) test_producer_connectivity ;;
            11) check_kafka_config ;;
            12) check_topic_config ;;
            13) show_troubleshooting_tips ;;
            14) run_all_checks ;;
            0) 
                echo -e "${GREEN}${SUCCESS} Exiting debug commands${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}${ERROR} Invalid option. Please select 0-14.${NC}"
                ;;
        esac
        
        echo ""
        read -p "Press Enter to continue..."
        echo ""
    done
}

# Check if script is run with arguments
if [ $# -eq 0 ]; then
    main
else
    case $1 in
        "containers") check_docker_containers ;;
        "connectivity") check_kafka_connectivity ;;
        "topics") list_kafka_topics ;;
        "consumers") check_consumer_groups ;;
        "messages") view_recent_messages ;;
        "offsets") check_topic_offsets ;;
        "logs") check_kafka_logs ;;
        "network") check_network_connectivity ;;
        "python") check_python_dependencies ;;
        "producer") test_producer_connectivity ;;
        "config") check_kafka_config ;;
        "topic-config") check_topic_config ;;
        "tips") show_troubleshooting_tips ;;
        "all") run_all_checks ;;
        *)
            echo -e "${RED}${ERROR} Unknown command: $1${NC}"
            echo "Available commands: containers, connectivity, topics, consumers, messages, offsets, logs, network, python, producer, config, topic-config, tips, all"
            exit 1
            ;;
    esac
fi 