#!/bin/bash

echo "🧹 Cleaning up duplicate directories..."

# Remove the entire tests/sre-kafka-streaming directory since it's a complete duplicate
echo "Removing tests/sre-kafka-streaming/ (complete duplicate of root)..."
rm -rf tests/sre-kafka-streaming/

# Remove the streaming/sre-kafka-streaming directory since it's also a duplicate
echo "Removing streaming/sre-kafka-streaming/ (another duplicate)..."
rm -rf streaming/sre-kafka-streaming/

# Keep the unique streaming/kafka directory
echo "Keeping streaming/kafka/ (unique content)..."

# Keep only the main directories in root
echo "✅ Keeping main directories:"
echo "  - agents/"
echo "  - config/"
echo "  - frontend/"
echo "  - orchestration/"
echo "  - ml_pipeline/"
echo "  - scripts/"
echo "  - data/"
echo "  - logs/"

echo "🧹 Cleanup complete!"
echo "📁 Remaining structure:"
tree -L 2 -I '__pycache__|*.pyc|*.log|*.pid|.git'
