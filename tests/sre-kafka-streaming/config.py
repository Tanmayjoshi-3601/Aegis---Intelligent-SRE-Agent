#!/usr/bin/env python3
"""
Configuration for the SRE Agent System
"""

import os

# Kafka Configuration
KAFKA_CONFIG = {
    'bootstrap_servers': '127.0.0.1:9093',
    'topic': 'system-logs',
    'group_id': 'sre-agent-group',
    'auto_offset_reset': 'latest'
}

# Storage Configuration
STORAGE_CONFIG = {
    'database_path': 'data/sre_agent.db',
    'logs_path': 'data/logs',
    'models_path': 'ml_pipeline/saved_models'
}

# ML Configuration
ML_CONFIG = {
    'model_path': 'ml_pipeline/saved_models/anomaly_detector.pkl',
    'scaler_path': 'ml_pipeline/saved_models/scaler.pkl',
    'encoder_path': 'ml_pipeline/saved_models/service_encoder.pkl',
    'threshold': 0.7,
    'use_ml': True
}

# Agent Configuration
AGENT_CONFIG = {
    'anomaly_detection': {
        'enabled': True,
        'confidence_threshold': 0.7
    },
    'rag_agent': {
        'enabled': True,
        'knowledge_base_path': 'data/knowledge_base'
    },
    'mitigation_agent': {
        'enabled': True,
        'validation_enabled': True
    }
}

# Twilio Configuration (for Paging Agent)
TWILIO_CONFIG = {
    'account_sid': 'ACd8962b295f0a17e1636ea572cc4f8769',
    'auth_token': 'a572e1b18df0419b273e32844d61f367',
    'from_number': '+13513005564',
    'to_number': os.getenv('SRE_ONCALL_PHONE', '+18573357165'),  # Updated to the new number
    'enabled': True
}

# SendGrid Configuration (for Report Generation Agent)
SENDGRID_CONFIG = {
    'api_key': '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',
    'from_email': os.getenv('SRE_SENDER_EMAIL', 'khanna.ka@northeastern.edu'),
    'to_email': 'xaviers3601@gmail.com',
    'enabled': True
}

# Dashboard Configuration
DASHBOARD_CONFIG = {
    'port': 8082,
    'debug': True,
    'host': '0.0.0.0'
} 