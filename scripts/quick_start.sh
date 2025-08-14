#!/bin/bash

# Aegis SRE Agent - Quick Start Script
# This script helps you get started with the new organized structure

set -e

echo "🛡️  Aegis SRE Agent - Quick Start"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -f "README.md" ] || [ ! -f "Dockerfile" ]; then
    echo "❌ Error: Please run this script from the Aegis---Intelligent-SRE-Agent root directory"
    exit 1
fi

echo "📁 Current project structure:"
echo "├── orchestration/     # Core orchestration engine"
echo "├── agents/            # Individual agent implementations"
echo "├── ml_pipeline/       # ML models and training"
echo "├── streaming/         # Kafka integration"
echo "├── communications/    # Voice and email systems"
echo "├── frontend/          # Dashboard UI"
echo "├── data/              # Synthetic data and knowledge base"
echo "├── tests/             # Test suites"
echo "├── config/            # Configuration files"
echo "├── scripts/           # Setup and utility scripts"
echo "├── logs/              # Application logs"
echo "├── docs/              # Documentation"
echo "├── Dockerfile         # Container configuration"
echo "└── README.md          # Main documentation"
echo ""

echo "🚀 Quick Start Options:"
echo "1. Complete setup (install, generate data, train models)"
echo "2. Start development environment"
echo "3. Start dashboard only"
echo "4. Run tests"
echo "5. View project structure"
echo "6. Exit"
echo ""

read -p "Choose an option (1-6): " choice

case $choice in
    1)
        echo "🔧 Running complete setup..."
        cd scripts
        make setup
        ;;
    2)
        echo "🛠️  Starting development environment..."
        cd scripts
        make dev
        ;;
    3)
        echo "📊 Starting dashboard..."
        cd scripts
        make start-dashboard
        ;;
    4)
        echo "🧪 Running tests..."
        cd scripts
        make test
        ;;
    5)
        echo "📁 Project structure:"
        echo ""
        echo "Key files and their new locations:"
        echo "├── config.py → orchestration/config.py"
        echo "├── dashboard_server_simple.py → orchestration/dashboard_server_simple.py"
        echo "├── requirements.txt → config/requirements.txt"
        echo "├── docker-compose.yml → config/docker-compose.yml"
        echo "├── start_*.sh → scripts/start_*.sh"
        echo "├── test_*.py → tests/test_*.py"
        echo "└── *.md → docs/*.md"
        echo ""
        echo "Available commands (run from scripts/ directory):"
        echo "├── make help          # Show all available commands"
        echo "├── make setup         # Complete setup"
        echo "├── make dev           # Start development environment"
        echo "├── make start-dashboard # Start dashboard"
        echo "├── make test          # Run tests"
        echo "└── make status        # Check system status"
        ;;
    6)
        echo "👋 Goodbye!"
        exit 0
        ;;
    *)
        echo "❌ Invalid option. Please choose 1-6."
        exit 1
        ;;
esac

echo ""
echo "✅ Done! Check the README.md for detailed documentation." 