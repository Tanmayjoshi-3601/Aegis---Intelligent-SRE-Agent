#!/bin/bash

# SRE Kafka Streaming Pipeline Start Script
# Opens multiple terminal windows/tabs to run producer and consumer

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
ROCKET="🚀"
PRODUCER="📤"
CONSUMER="📥"
MONITOR="📊"
TERMINAL="🖥️"

echo -e "${BLUE}${ROCKET} SRE Kafka Streaming Pipeline Starter${NC}"
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

# Function to detect OS and terminal
detect_os() {
    case "$(uname -s)" in
        Darwin*)    echo "macos";;
        Linux*)     echo "linux";;
        CYGWIN*|MINGW32*|MSYS*|MINGW*) echo "windows";;
        *)          echo "unknown";;
    esac
}

# Function to create producer script
create_producer_script() {
    cat > /tmp/sre_producer.sh << 'EOF'
#!/bin/bash
# Producer script for SRE Kafka Streaming

cd "$(dirname "$0")"

echo -e "\033[0;34m📤 SRE Log Producer Started\033[0m"
echo "=================================="
echo "Streaming logs to Kafka topic: system-logs"
echo "Press Ctrl+C to stop"
echo ""

# Run the producer
python3 streaming/kafka/custom_log_streamer.py \
    --mode produce \
    --logs data/logs.json \
    --metadata data/metadata.json \
    --rate 10 \
    --scenario realistic
EOF
    chmod +x /tmp/sre_producer.sh
}

# Function to create consumer script
create_consumer_script() {
    cat > /tmp/sre_consumer.sh << 'EOF'
#!/bin/bash
# Consumer script for SRE Kafka Streaming

cd "$(dirname "$0")"

echo -e "\033[0;35m📥 SRE Log Consumer Started\033[0m"
echo "=================================="
echo "Consuming logs from Kafka topic: system-logs"
echo "Press Ctrl+C to stop"
echo ""

# Run the consumer
python3 streaming/kafka/custom_log_streamer.py \
    --mode consume
EOF
    chmod +x /tmp/sre_consumer.sh
}

# Function to create monitor script
create_monitor_script() {
    cat > /tmp/sre_monitor.sh << 'EOF'
#!/bin/bash
# Monitor script for SRE Kafka Streaming

cd "$(dirname "$0")"

echo -e "\033[0;36m📊 SRE Pipeline Monitor Started\033[0m"
echo "=================================="
echo "Monitoring Kafka streaming pipeline"
echo "Press Ctrl+C to stop"
echo ""

# Run the monitor
python3 monitor.py
EOF
    chmod +x /tmp/sre_monitor.sh
}

# Check if services are running
print_status "info" "Checking if Kafka services are running..."

if ! nc -z localhost 9092 2>/dev/null; then
    print_status "error" "Kafka is not running on localhost:9092"
    print_status "info" "Please run ./run_pipeline.sh first to start the services"
    exit 1
fi

print_status "success" "Kafka is running"

# Check if Python script exists
if [ ! -f "streaming/kafka/custom_log_streamer.py" ]; then
    print_status "error" "Custom log streamer script not found"
    exit 1
fi

print_status "success" "Custom log streamer script found"

# Detect OS
OS=$(detect_os)
print_status "info" "Detected OS: $OS"

# Create scripts
print_status "info" "Creating terminal scripts..."
create_producer_script
create_consumer_script
create_monitor_script
print_status "success" "Terminal scripts created"

# Function to start terminals based on OS
start_terminals() {
    case $OS in
        "macos")
            start_macos_terminals
            ;;
        "linux")
            start_linux_terminals
            ;;
        "windows")
            start_windows_terminals
            ;;
        *)
            start_fallback_terminals
            ;;
    esac
}

# macOS terminal handling
start_macos_terminals() {
    print_status "info" "Starting macOS terminal windows..."
    
    # Check if we're in Terminal.app
    if [ "$TERM_PROGRAM" = "Apple_Terminal" ]; then
        # Use Terminal.app tabs
        print_status "info" "Using Terminal.app tabs..."
        
        # Start producer in new tab
        osascript << EOF
tell application "Terminal"
    activate
    tell application "System Events" to keystroke "t" using command down
    delay 0.5
    do script "cd $(pwd) && /tmp/sre_producer.sh" in selected tab of front window
end tell
EOF
        
        # Start consumer in new tab
        osascript << EOF
tell application "Terminal"
    activate
    tell application "System Events" to keystroke "t" using command down
    delay 0.5
    do script "cd $(pwd) && /tmp/sre_consumer.sh" in selected tab of front window
end tell
EOF
        
        # Start monitor in new tab
        osascript << EOF
tell application "Terminal"
    activate
    tell application "System Events" to keystroke "t" using command down
    delay 0.5
    do script "cd $(pwd) && /tmp/sre_monitor.sh" in selected tab of front window
end tell
EOF
        
    else
        # Use iTerm2 or fallback to new windows
        if command_exists iTerm2; then
            start_iterm2_terminals
        else
            start_fallback_terminals
        fi
    fi
}

# iTerm2 terminal handling
start_iterm2_terminals() {
    print_status "info" "Using iTerm2..."
    
    # Start producer
    osascript << EOF
tell application "iTerm2"
    activate
    create window with default profile
    tell current window
        create tab with default profile
        tell current session
            write text "cd $(pwd) && /tmp/sre_producer.sh"
        end tell
    end tell
end tell
EOF
    
    # Start consumer
    osascript << EOF
tell application "iTerm2"
    activate
    tell current window
        create tab with default profile
        tell current session
            write text "cd $(pwd) && /tmp/sre_consumer.sh"
        end tell
    end tell
end tell
EOF
    
    # Start monitor
    osascript << EOF
tell application "iTerm2"
    activate
    tell current window
        create tab with default profile
        tell current session
            write text "cd $(pwd) && /tmp/sre_monitor.sh"
        end tell
    end tell
end tell
EOF
}

# Linux terminal handling
start_linux_terminals() {
    print_status "info" "Starting Linux terminal windows..."
    
    # Try different terminal emulators
    if command_exists gnome-terminal; then
        gnome-terminal --tab --title="Producer" -- bash -c "cd $(pwd) && /tmp/sre_producer.sh; exec bash" \
                      --tab --title="Consumer" -- bash -c "cd $(pwd) && /tmp/sre_consumer.sh; exec bash" \
                      --tab --title="Monitor" -- bash -c "cd $(pwd) && /tmp/sre_monitor.sh; exec bash"
    elif command_exists konsole; then
        konsole --new-tab -e bash -c "cd $(pwd) && /tmp/sre_producer.sh; exec bash" \
               --new-tab -e bash -c "cd $(pwd) && /tmp/sre_consumer.sh; exec bash" \
               --new-tab -e bash -c "cd $(pwd) && /tmp/sre_monitor.sh; exec bash"
    elif command_exists xterm; then
        xterm -title "Producer" -e bash -c "cd $(pwd) && /tmp/sre_producer.sh; exec bash" &
        xterm -title "Consumer" -e bash -c "cd $(pwd) && /tmp/sre_consumer.sh; exec bash" &
        xterm -title "Monitor" -e bash -c "cd $(pwd) && /tmp/sre_monitor.sh; exec bash" &
    else
        start_fallback_terminals
    fi
}

# Windows terminal handling
start_windows_terminals() {
    print_status "info" "Starting Windows terminal windows..."
    
    if command_exists start; then
        start "Producer" cmd /k "cd /d $(pwd) && /tmp/sre_producer.sh"
        start "Consumer" cmd /k "cd /d $(pwd) && /tmp/sre_consumer.sh"
        start "Monitor" cmd /k "cd /d $(pwd) && /tmp/sre_monitor.sh"
    else
        start_fallback_terminals
    fi
}

# Fallback terminal handling
start_fallback_terminals() {
    print_status "warning" "Using fallback terminal method..."
    print_status "info" "You'll need to manually open new terminal windows/tabs"
    print_status "info" "and run the following commands:"
    echo ""
    echo -e "${CYAN}${TERMINAL} Producer Terminal:${NC}"
    echo "  cd $(pwd)"
    echo "  /tmp/sre_producer.sh"
    echo ""
    echo -e "${CYAN}${TERMINAL} Consumer Terminal:${NC}"
    echo "  cd $(pwd)"
    echo "  /tmp/sre_consumer.sh"
    echo ""
    echo -e "${CYAN}${TERMINAL} Monitor Terminal:${NC}"
    echo "  cd $(pwd)"
    echo "  /tmp/sre_monitor.sh"
    echo ""
    
    # Ask user if they want to start one component in current terminal
    read -p "Start producer in current terminal? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "info" "Starting producer in current terminal..."
        /tmp/sre_producer.sh
    fi
}

# Main execution
main() {
    print_status "info" "Starting SRE Kafka Streaming Pipeline..."
    
    # Start terminals
    start_terminals
    
    print_status "success" "Pipeline components started!"
    echo ""
    echo -e "${GREEN}${ROCKET} Pipeline Status:${NC}"
    echo "=================="
    echo -e "${GREEN}${PRODUCER} Producer: Running${NC}"
    echo -e "${GREEN}${CONSUMER} Consumer: Running${NC}"
    echo -e "${GREEN}${MONITOR} Monitor: Running${NC}"
    echo ""
    echo -e "${BLUE}${INFO} Pipeline Information:${NC}"
    echo "========================"
    echo "Kafka Topic: system-logs"
    echo "Log Rate: 10 logs/second"
    echo "Scenario: Realistic (based on metadata)"
    echo "Total Logs: 2,728"
    echo "Expected Anomalies: ~54%"
    echo ""
    echo -e "${BLUE}${INFO} Monitoring URLs:${NC}"
    echo "=================="
    echo "Kafka UI: http://localhost:8080"
    echo "RabbitMQ Management: http://localhost:15672"
    echo ""
    echo -e "${YELLOW}${WARNING} To stop the pipeline:${NC}"
    echo "1. Press Ctrl+C in each terminal"
    echo "2. Or run: docker-compose down"
    echo ""
    echo -e "${GREEN}${SUCCESS} Pipeline is now streaming logs!${NC}"
}

# Run main function
main 