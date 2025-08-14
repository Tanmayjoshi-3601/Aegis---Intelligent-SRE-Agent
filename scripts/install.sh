#!/bin/bash

# SRE Kafka Streaming Pipeline Installation Script
# Sets up the environment and installs dependencies

set -e

# Colors and emojis
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

SUCCESS="✅"
ERROR="❌"
WARNING="⚠️"
INFO="ℹ️"
INSTALL="📦"
CHECK="🔍"

echo -e "${BLUE}${INSTALL} SRE Kafka Streaming Pipeline Installation${NC}"
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

# Function to check Docker installation
check_docker() {
    print_status "info" "Checking Docker installation..."
    
    if ! command_exists docker; then
        print_status "error" "Docker is not installed"
        print_status "info" "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
        return 1
    fi
    
    if ! docker info >/dev/null 2>&1; then
        print_status "error" "Docker is not running"
        print_status "info" "Please start Docker Desktop"
        return 1
    fi
    
    print_status "success" "Docker is installed and running"
    return 0
}

# Function to check Python installation
check_python() {
    print_status "info" "Checking Python installation..."
    
    if ! command_exists python3; then
        print_status "error" "Python 3 is not installed"
        print_status "info" "Please install Python 3.8+ from: https://www.python.org/downloads/"
        return 1
    fi
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_status "success" "Python $python_version is installed"
    
    # Check if version is 3.8+
    major=$(echo $python_version | cut -d'.' -f1)
    minor=$(echo $python_version | cut -d'.' -f2)
    
    if [ "$major" -lt 3 ] || ([ "$major" -eq 3 ] && [ "$minor" -lt 8 ]); then
        print_status "warning" "Python version $python_version detected. Python 3.8+ is recommended."
    fi
    
    return 0
}

# Function to install Python dependencies
install_python_deps() {
    print_status "info" "Installing Python dependencies..."
    
    # Check if pip is available
    if ! command_exists pip3; then
        print_status "error" "pip3 is not available"
        print_status "info" "Please install pip: python3 -m ensurepip --upgrade"
        return 1
    fi
    
    # Install dependencies from requirements.txt
    if [ -f "requirements.txt" ]; then
        print_status "info" "Installing from requirements.txt..."
        pip3 install -r requirements.txt
        print_status "success" "Python dependencies installed"
    else
        # Install kafka-python directly
        print_status "info" "Installing kafka-python..."
        pip3 install kafka-python>=2.0.2
        print_status "success" "kafka-python installed"
    fi
    
    return 0
}

# Function to make scripts executable
make_executable() {
    print_status "info" "Making scripts executable..."
    
    scripts=("run_pipeline.sh" "start_streaming.sh" "debug_commands.sh" "cleanup.sh" "test_streaming.py" "monitor.py")
    
    for script in "${scripts[@]}"; do
        if [ -f "$script" ]; then
            chmod +x "$script"
            print_status "success" "Made $script executable"
        else
            print_status "warning" "Script $script not found"
        fi
    done
}

# Function to verify installation
verify_installation() {
    print_status "info" "Verifying installation..."
    
    # Check if key files exist
    required_files=("docker-compose.yml" "streaming/kafka/custom_log_streamer.py" "data/logs.json" "data/metadata.json")
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            print_status "success" "Found $file"
        else
            print_status "error" "Missing required file: $file"
            return 1
        fi
    done
    
    # Test Python import
    if python3 -c "import kafka" 2>/dev/null; then
        print_status "success" "kafka-python import test passed"
    else
        print_status "error" "kafka-python import test failed"
        return 1
    fi
    
    return 0
}

# Function to show next steps
show_next_steps() {
    echo ""
    echo -e "${CYAN}${CHECK} Installation Complete!${NC}"
    echo "========================"
    echo ""
    echo -e "${GREEN}${SUCCESS} Next Steps:${NC}"
    echo "1. Start the pipeline: ./run_pipeline.sh"
    echo "2. Test the setup: python3 test_streaming.py"
    echo "3. Start streaming: ./start_streaming.sh"
    echo "4. Monitor the pipeline: python3 monitor.py"
    echo ""
    echo -e "${BLUE}${INFO} Useful Commands:${NC}"
    echo "- Debug issues: ./debug_commands.sh"
    echo "- Clean up: ./cleanup.sh"
    echo "- View logs: docker-compose logs -f [service-name]"
    echo ""
    echo -e "${YELLOW}${WARNING} Important URLs:${NC}"
    echo "- Kafka UI: http://localhost:8080"
    echo "- RabbitMQ Management: http://localhost:15672"
    echo ""
    echo -e "${GREEN}${SUCCESS} Happy streaming! 🚀${NC}"
}

# Main installation function
main() {
    print_status "info" "Starting installation process..."
    
    # Check prerequisites
    if ! check_docker; then
        print_status "error" "Docker check failed. Please install and start Docker Desktop."
        exit 1
    fi
    
    if ! check_python; then
        print_status "error" "Python check failed. Please install Python 3.8+."
        exit 1
    fi
    
    # Install Python dependencies
    if ! install_python_deps; then
        print_status "error" "Python dependencies installation failed."
        exit 1
    fi
    
    # Make scripts executable
    make_executable
    
    # Verify installation
    if ! verify_installation; then
        print_status "error" "Installation verification failed."
        exit 1
    fi
    
    # Show next steps
    show_next_steps
}

# Run main function
main 