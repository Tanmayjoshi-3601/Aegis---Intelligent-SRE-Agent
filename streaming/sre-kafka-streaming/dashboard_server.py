#!/usr/bin/env python3
"""
SRE Agent Dashboard Server
Flask server to serve the dashboard frontend and provide API endpoints
Connected to real Kafka streaming and SRE agent system
"""

import os
import json
import time
import random
import asyncio
import threading
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import sqlite3
from pathlib import Path
from kafka import KafkaConsumer
import logging

# Import our SRE agent components
from sre_agent_orchestrator import SREAgentOrchestrator, LogEntry
from orchestration.validation_simulator import MitigationSimulator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='frontend', template_folder='frontend')
CORS(app)

# Configuration
DASHBOARD_CONFIG = {
    'port': 8081,
    'debug': True,
    'host': '0.0.0.0'
}

# Kafka Configuration
KAFKA_CONFIG = {
    'bootstrap_servers': ['localhost:9092'],
    'topic': 'sre-logs',
    'group_id': 'dashboard-consumer',
    'auto_offset_reset': 'latest',
    'enable_auto_commit': True,
    'value_deserializer': lambda x: json.loads(x.decode('utf-8'))
}

# Global state for real-time data
class DashboardState:
    def __init__(self):
        self.logs_processed = 0
        self.anomalies_detected = 0
        self.auto_resolved = 0
        self.pages_sent = 0
        self.recent_logs = []
        self.agent_decisions = []
        self.mitigation_actions = []
        self.active_anomalies = []
        self.system_status = 'healthy'
        self.last_update = datetime.now()
        
        # Initialize SRE Agent components
        self.orchestrator = None
        self.simulator = MitigationSimulator()
        self.kafka_consumer = None
        self.kafka_thread = None
        self.is_running = False

# Global dashboard state
dashboard_state = DashboardState()

def initialize_sre_agents():
    """Initialize the SRE agent system"""
    try:
        logger.info("🔧 Initializing SRE Agent System...")
        dashboard_state.orchestrator = SREAgentOrchestrator()
        logger.info("✅ SRE Agent System initialized")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to initialize SRE Agent System: {e}")
        return False

def process_log_through_sre_agents(log_data):
    """Process a log through the SRE agent system"""
    try:
        if dashboard_state.orchestrator:
            # Process through orchestrator
            result = asyncio.run(dashboard_state.orchestrator.process_log(log_data))
            
            # Update dashboard state based on result
            dashboard_state.logs_processed += 1
            
            # Check for anomalies
            decisions = result.get('decisions', [])
            for decision in decisions:
                if decision.decision == 'anomaly':
                    dashboard_state.anomalies_detected += 1
                    dashboard_state.active_anomalies.append({
                        'id': log_data.get('request_id', 'unknown'),
                        'service': log_data.get('service', 'unknown'),
                        'timestamp': log_data.get('timestamp', datetime.now().isoformat()),
                        'level': log_data.get('level', 'INFO'),
                        'message': log_data.get('message', 'Anomaly detected')
                    })
            
            # Check actions taken
            actions = result.get('actions_taken', [])
            for action in actions:
                if action.get('action') == 'store_log':
                    # Normal log stored
                    pass
                elif action.get('status') == 'success':
                    dashboard_state.auto_resolved += 1
                elif action.get('action') == 'send_page':
                    dashboard_state.pages_sent += 1
            
            # Add to recent logs
            log_entry = {
                'timestamp': log_data.get('timestamp', datetime.now().isoformat()),
                'service': log_data.get('service', 'unknown'),
                'level': log_data.get('level', 'INFO'),
                'message': log_data.get('message', ''),
                'anomaly': any(d.decision == 'anomaly' for d in decisions),
                'processing_result': result
            }
            
            dashboard_state.recent_logs.insert(0, log_entry)
            
            # Keep only last 100 logs
            if len(dashboard_state.recent_logs) > 100:
                dashboard_state.recent_logs = dashboard_state.recent_logs[:100]
            
            # Update system status
            if dashboard_state.anomalies_detected > 0:
                dashboard_state.system_status = 'warning'
            if dashboard_state.pages_sent > 0:
                dashboard_state.system_status = 'critical'
            
            dashboard_state.last_update = datetime.now()
            
            logger.info(f"✅ Processed log {log_data.get('request_id', 'unknown')} through SRE agents")
            
    except Exception as e:
        logger.error(f"❌ Error processing log through SRE agents: {e}")

def kafka_consumer_thread():
    """Background thread to consume Kafka messages"""
    try:
        logger.info("🔄 Starting Kafka consumer thread...")
        
        # Initialize Kafka consumer
        consumer = KafkaConsumer(**KAFKA_CONFIG)
        consumer.subscribe([KAFKA_CONFIG['topic']])
        
        dashboard_state.kafka_consumer = consumer
        dashboard_state.is_running = True
        
        logger.info(f"✅ Kafka consumer connected to topic: {KAFKA_CONFIG['topic']}")
        
        for message in consumer:
            if not dashboard_state.is_running:
                break
                
            try:
                log_data = message.value
                logger.info(f"📨 Received log: {log_data.get('request_id', 'unknown')}")
                
                # Process through SRE agents
                process_log_through_sre_agents(log_data)
                
            except Exception as e:
                logger.error(f"❌ Error processing Kafka message: {e}")
        
        consumer.close()
        logger.info("🛑 Kafka consumer thread stopped")
        
    except Exception as e:
        logger.error(f"❌ Kafka consumer thread error: {e}")

def start_kafka_streaming():
    """Start Kafka streaming in background thread"""
    if dashboard_state.kafka_thread is None or not dashboard_state.kafka_thread.is_alive():
        dashboard_state.kafka_thread = threading.Thread(target=kafka_consumer_thread, daemon=True)
        dashboard_state.kafka_thread.start()
        logger.info("🚀 Kafka streaming started")

def stop_kafka_streaming():
    """Stop Kafka streaming"""
    dashboard_state.is_running = False
    if dashboard_state.kafka_consumer:
        dashboard_state.kafka_consumer.close()
    logger.info("🛑 Kafka streaming stopped")

# Flask Routes
@app.route('/')
def dashboard():
    """Serve the main dashboard"""
    return render_template('index.html')

@app.route('/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('frontend', filename)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'kafka_connected': dashboard_state.is_running,
        'sre_agents_initialized': dashboard_state.orchestrator is not None
    })

@app.route('/api/dashboard/metrics')
def get_metrics():
    """Get current dashboard metrics"""
    return jsonify({
        'logsProcessed': dashboard_state.logs_processed,
        'anomaliesDetected': dashboard_state.anomalies_detected,
        'autoResolved': dashboard_state.auto_resolved,
        'pagesSent': dashboard_state.pages_sent,
        'systemStatus': dashboard_state.system_status,
        'lastUpdate': dashboard_state.last_update.isoformat()
    })

@app.route('/api/agents/status')
def get_agent_status():
    """Get agent status"""
    agents = []
    
    if dashboard_state.orchestrator:
        for agent_name, agent in dashboard_state.orchestrator.agents.items():
            agents.append({
                'name': agent_name.replace('_', ' ').title(),
                'status': 'online',
                'lastSeen': datetime.now().isoformat(),
                'version': '1.0.0'
            })
    
    return jsonify({'agents': agents})

@app.route('/api/logs/recent')
def get_recent_logs():
    """Get recent logs"""
    return jsonify({
        'logs': dashboard_state.recent_logs[-20:],  # Last 20 logs
        'total': len(dashboard_state.recent_logs)
    })

@app.route('/api/anomalies/active')
def get_active_anomalies():
    """Get active anomalies"""
    return jsonify({
        'anomalies': dashboard_state.active_anomalies,
        'count': len(dashboard_state.active_anomalies)
    })

@app.route('/api/trigger-anomaly', methods=['POST'])
def trigger_anomaly():
    """Trigger a test anomaly"""
    try:
        data = request.get_json()
        anomaly_type = data.get('type', 'cpu_overload')
        
        # Create test log based on anomaly type
        test_log = create_test_anomaly_log(anomaly_type)
        
        # Process through SRE agents
        process_log_through_sre_agents(test_log)
        
        return jsonify({
            'success': True,
            'message': f'Anomaly {anomaly_type} triggered successfully',
            'log_id': test_log.get('request_id')
        })
        
    except Exception as e:
        logger.error(f"❌ Error triggering anomaly: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def create_test_anomaly_log(anomaly_type):
    """Create a test log entry for the specified anomaly type"""
    base_log = {
        'timestamp': datetime.now().isoformat(),
        'request_id': f'req_test_{anomaly_type}_{int(time.time())}',
        'host': f'test-host-{anomaly_type}.prod.internal',
        'environment': 'production',
        'anomaly': True
    }
    
    if anomaly_type == 'cpu_overload':
        base_log.update({
            'service': 'web-service',
            'level': 'ERROR',
            'message': 'High CPU usage detected',
            'metrics': {
                'cpu_usage': 95.5,
                'memory_usage': 78.3,
                'error_rate': 0.08,
                'request_latency_ms': 4500,
                'active_connections': 380
            }
        })
    elif anomaly_type == 'memory_leak':
        base_log.update({
            'service': 'api-gateway',
            'level': 'ERROR',
            'message': 'Memory usage spike detected',
            'metrics': {
                'cpu_usage': 45.2,
                'memory_usage': 92.1,
                'error_rate': 0.05,
                'request_latency_ms': 3200,
                'active_connections': 250
            }
        })
    elif anomaly_type == 'database_slowdown':
        base_log.update({
            'service': 'database-primary',
            'level': 'ERROR',
            'message': 'Database performance degradation',
            'metrics': {
                'cpu_usage': 35.1,
                'memory_usage': 45.8,
                'request_latency_ms': 8000,
                'error_rate': 0.12,
                'active_connections': 1200
            }
        })
    elif anomaly_type == 'service_crash':
        base_log.update({
            'service': 'critical-service',
            'level': 'CRITICAL',
            'message': 'Critical service failure',
            'metrics': {
                'cpu_usage': 98.5,
                'memory_usage': 95.2,
                'error_rate': 0.25,
                'request_latency_ms': 15000,
                'active_connections': 1500
            }
        })
    else:
        # Default anomaly
        base_log.update({
            'service': 'unknown-service',
            'level': 'ERROR',
            'message': 'Unknown anomaly detected',
            'metrics': {
                'cpu_usage': 85.0,
                'memory_usage': 80.0,
                'error_rate': 0.10,
                'request_latency_ms': 5000,
                'active_connections': 500
            }
        })
    
    return base_log

@app.route('/api/reset-system', methods=['POST'])
def reset_system():
    """Reset the system state"""
    try:
        dashboard_state.logs_processed = 0
        dashboard_state.anomalies_detected = 0
        dashboard_state.auto_resolved = 0
        dashboard_state.pages_sent = 0
        dashboard_state.recent_logs = []
        dashboard_state.agent_decisions = []
        dashboard_state.mitigation_actions = []
        dashboard_state.active_anomalies = []
        dashboard_state.system_status = 'healthy'
        dashboard_state.last_update = datetime.now()
        
        return jsonify({
            'success': True,
            'message': 'System reset successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Error resetting system: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting SRE Agent Dashboard Server...")
    print(f"📊 Dashboard will be available at: http://localhost:{DASHBOARD_CONFIG['port']}")
    print(f"🔧 API endpoints available at: http://localhost:{DASHBOARD_CONFIG['port']}/api/")
    print(f"📁 Static files served from: {os.path.abspath('frontend')}")
    print(f"🐛 Debug mode: {DASHBOARD_CONFIG['debug']}")
    
    # Initialize SRE agents
    if initialize_sre_agents():
        print("✅ SRE Agent System initialized successfully")
    else:
        print("⚠️  SRE Agent System initialization failed - using mock data")
    
    # Start Kafka streaming
    try:
        start_kafka_streaming()
        print("✅ Kafka streaming started")
    except Exception as e:
        print(f"⚠️  Kafka streaming failed: {e}")
        print("📝 Using test anomaly triggers instead")
    
    # Start Flask server
    app.run(
        host=DASHBOARD_CONFIG['host'],
        port=DASHBOARD_CONFIG['port'],
        debug=DASHBOARD_CONFIG['debug']
    ) 