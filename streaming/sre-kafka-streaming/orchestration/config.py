"""
Orchestration Configuration
===========================
Central configuration for the SRE agent orchestration layer
"""

import os
from pathlib import Path

# Kafka Configuration
KAFKA_CONFIG = {
    'bootstrap_servers': '127.0.0.1:9093',
    'topics': {
        'input': 'system-logs',
        'anomalies': 'anomaly-alerts',
        'normal': 'normal-logs'
    },
    'consumer': {
        'group_id': 'sre-orchestrator',
        'auto_offset_reset': 'latest',
        'enable_auto_commit': True,
        'max_poll_records': 10
    }
}

# Storage Configuration
STORAGE_CONFIG = {
    'logs_dir': Path('orchestration_output'),
    'normal_logs': Path('orchestration_output/normal_logs'),
    'anomaly_logs': Path('orchestration_output/anomaly_logs'),
    'decisions': Path('orchestration_output/decisions')
}

# Create directories if they don't exist
for path in STORAGE_CONFIG.values():
    path.mkdir(parents=True, exist_ok=True)

# ML Model Configuration
ML_CONFIG = {
    'model_path': 'ml_pipeline/saved_models/',
    'confidence_threshold': 0.5
}

# Agent Configuration
AGENT_CONFIG = {
    'timeout': 30,  # seconds
    'retry_count': 3
}

# Logging Configuration
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s' 