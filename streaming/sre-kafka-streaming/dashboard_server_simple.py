#!/usr/bin/env python3
"""
Simplified SRE Agent Dashboard Server
Flask server with real log streaming and anomaly processing
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
import logging

# Import our SRE agent components (without database)
from orchestration.validation_simulator import MitigationSimulator, RAGMitigationStrategies
from agents.rag_agent import RAGAgent
from agents.mitigation_agent import MitigationAgent
from agents.report_generation_agent import ReportGenerationAgent
from agents.paging_agent import PagingAgent
from ml_orchestrator import MLOrchestrator
from config import TWILIO_CONFIG, SENDGRID_CONFIG

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='frontend', template_folder='frontend')
CORS(app)

# Configuration
DASHBOARD_CONFIG = {
    'port': 8082,
    'debug': True,
    'host': '0.0.0.0'
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
        
        # Initialize SRE Agent components (without orchestrator)
        self.rag_agent = None
        self.mitigation_agent = None
        self.report_agent = None
        self.paging_agent = None
        self.ml_orchestrator = None  # Add ML orchestrator
        self.simulator = MitigationSimulator()
        self.is_running = False
        self.last_detection_result = None # Added for frontend

# Global dashboard state
dashboard_state = DashboardState()

def initialize_sre_agents():
    """Initialize the SRE agent components"""
    try:
        logger.info("🔧 Initializing SRE Agent Components...")
        
        # Initialize ML Orchestrator (for real anomaly detection)
        dashboard_state.ml_orchestrator = MLOrchestrator()
        logger.info("✅ ML Orchestrator initialized")
        
        # Initialize RAG Agent
        dashboard_state.rag_agent = RAGAgent()
        logger.info("✅ RAG Agent initialized")
        
        # Initialize Mitigation Agent
        dashboard_state.mitigation_agent = MitigationAgent()
        logger.info("✅ Mitigation Agent initialized")
        
        # Initialize Report Generation Agent with SendGrid config
        dashboard_state.report_agent = ReportGenerationAgent(SENDGRID_CONFIG)
        logger.info("✅ Report Generation Agent initialized")
        
        # Initialize Paging Agent with Twilio config
        dashboard_state.paging_agent = PagingAgent(TWILIO_CONFIG)
        logger.info("✅ Paging Agent initialized")
        
        logger.info("✅ SRE Agent Components initialized")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize SRE Agent Components: {e}")
        return False

async def process_log_through_sre_agents(log_data):
    """Process a log through the SRE agent system"""
    try:
        # Update dashboard state
        dashboard_state.logs_processed += 1
        
        # Create LogEntry for processing
        from sre_agent_orchestrator import LogEntry
        log_entry = LogEntry(
            timestamp=log_data.get('timestamp', datetime.now().isoformat()),
            service=log_data.get('service', 'unknown'),
            level=log_data.get('level', 'INFO'),
            request_id=log_data.get('request_id', 'unknown'),
            host=log_data.get('host', 'unknown'),
            environment=log_data.get('environment', 'production'),
            metrics=log_data.get('metrics', {}),
            anomaly=log_data.get('anomaly', False),
            message=log_data.get('message', '')
        )
        
        # Use ML Orchestrator for real anomaly detection
        # BUT: Synthetic logs should only be anomalies if explicitly triggered
        if dashboard_state.ml_orchestrator:
            # For synthetic logs, only use ML if it's a triggered anomaly
            if log_data.get('anomaly', False) or 'req_test_' in log_data.get('request_id', ''):
                # This is a triggered anomaly - use ML detection
                is_anomaly, confidence, explanation = dashboard_state.ml_orchestrator.detect_anomaly_ml(log_data)
                
                # Create anomaly decision from ML results
                anomaly_decision = {
                    'decision': 'anomaly' if is_anomaly else 'normal',
                    'confidence': confidence,
                    'reasoning': explanation.get('recommendation', 'ML model analysis') if explanation else 'Normal operation - no anomalies detected',
                    'ml_explanation': explanation
                }
            else:
                # This is a synthetic log - always treat as normal
                is_anomaly = False
                anomaly_decision = {
                    'decision': 'normal',
                    'confidence': 0.95,
                    'reasoning': 'Synthetic log - normal operation',
                    'ml_explanation': None
                }
        else:
            # Fallback to basic detection if ML orchestrator not available
            is_anomaly = log_data.get('anomaly', False)
            anomaly_decision = {
                'decision': 'anomaly' if is_anomaly else 'normal',
                'confidence': 0.85 if is_anomaly else 0.95,
                'reasoning': 'Anomaly detected based on metrics' if is_anomaly else 'Normal operation - no anomalies detected'
            }
        
        # Store detection result for frontend
        # Prioritize triggered anomalies for 30 seconds, then allow synthetic logs
        current_time = datetime.now()
        if is_anomaly or (dashboard_state.last_detection_result is None or 
                         (current_time - datetime.fromisoformat(dashboard_state.last_detection_result['timestamp'])).seconds > 30):
            dashboard_state.last_detection_result = {
                'timestamp': current_time.isoformat(),
                'is_anomaly': is_anomaly,
                'confidence': anomaly_decision['confidence'],
                'reasoning': anomaly_decision['reasoning'],
                'service': log_data.get('service', 'unknown'),
                'model_used': 'ML Model' if dashboard_state.ml_orchestrator and dashboard_state.ml_orchestrator.use_ml and (log_data.get('anomaly', False) or 'req_test_' in log_data.get('request_id', '')) else 'Synthetic Normal',
                'ml_explanation': anomaly_decision.get('ml_explanation')
            }
        
        # Process through RAG Agent only if anomaly detected
        if dashboard_state.rag_agent and is_anomaly:
            rag_result = await dashboard_state.rag_agent.process(log_entry, anomaly_decision)
            
            # Check if escalation is needed
            if not rag_result.get('needs_escalation', False):
                # Process through Mitigation Agent
                if dashboard_state.mitigation_agent:
                    mitigation_result = await dashboard_state.mitigation_agent.execute_mitigation(log_entry, rag_result)
                    
                    if mitigation_result.get('status') == 'success':
                        dashboard_state.auto_resolved += 1
                    else:
                        dashboard_state.pages_sent += 1
                else:
                    dashboard_state.auto_resolved += 1
            else:
                # ESCALATION PATH: RAG couldn't solve it, go to Advanced LLM + Report + Paging
                dashboard_state.pages_sent += 1
                
                # Simulate Advanced LLM processing (in real system, this would call the Advanced LLM Agent)
                advanced_llm_result = {
                    'summary': f'Critical issue detected in {log_data.get("service", "unknown")} service requiring immediate attention.',
                    'recommendations': [
                        'Immediately investigate the root cause',
                        'Check system resources and scaling',
                        'Review recent deployments',
                        'Monitor system recovery'
                    ],
                    'priority': 'critical'
                }
                
                # Generate and send report
                if dashboard_state.report_agent:
                    report_result = await dashboard_state.report_agent.generate_and_send_report(log_data, advanced_llm_result)
                    logger.info(f"📧 Report generation result: {report_result.get('status', 'unknown')}")
                
                # Page the SRE on-call
                if dashboard_state.paging_agent:
                    paging_result = await dashboard_state.paging_agent.page_sre_oncall(log_data)
                    logger.info(f"📞 Paging result: {paging_result.get('status', 'unknown')}")
            
            dashboard_state.anomalies_detected += 1
            
            # Add to active anomalies
            dashboard_state.active_anomalies.append({
                'id': log_data.get('request_id', 'unknown'),
                'service': log_data.get('service', 'unknown'),
                'timestamp': log_data.get('timestamp', datetime.now().isoformat()),
                'level': log_data.get('level', 'INFO'),
                'message': log_data.get('message', 'Anomaly detected'),
                'rag_result': rag_result
            })
        
        # Add to recent logs
        log_entry_display = {
            'timestamp': log_data.get('timestamp', datetime.now().isoformat()),
            'service': log_data.get('service', 'unknown'),
            'level': log_data.get('level', 'INFO'),
            'message': log_data.get('message', ''),
            'anomaly': is_anomaly,
            'request_id': log_data.get('request_id', 'unknown')
        }
        
        dashboard_state.recent_logs.insert(0, log_entry_display)
        
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

def generate_synthetic_logs():
    """Generate synthetic logs for demonstration"""
    services = ['web-service', 'api-gateway', 'database-primary', 'cache-service', 'load-balancer']
    levels = ['INFO', 'WARNING', 'ERROR']
    
    while dashboard_state.is_running:
        try:
            # Generate a random log
            service = random.choice(services)
            level = random.choice(levels)
            
            # Create log data - NO RANDOM ANOMALIES
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'service': service,
                'level': level,
                'request_id': f'req_synth_{int(time.time())}_{random.randint(1000, 9999)}',
                'host': f'{service}-{random.randint(1, 5)}.prod.internal',
                'environment': 'production',
                'message': f'Processing request for {service}',
                'metrics': {
                    'cpu_usage': random.uniform(20, 80),
                    'memory_usage': random.uniform(30, 85),
                    'error_rate': random.uniform(0, 0.05),
                    'request_latency_ms': random.uniform(50, 500),
                    'active_connections': random.randint(50, 800)
                },
                'anomaly': False  # Always false - anomalies only from presets
            }
            
            # Process the log through anomaly detection
            asyncio.run(process_log_through_sre_agents(log_data))
            
            # Wait between logs
            time.sleep(random.uniform(2, 8))
            
        except Exception as e:
            logger.error(f"❌ Error generating synthetic logs: {e}")
            time.sleep(5)

def start_synthetic_logging():
    """Start synthetic log generation in background thread"""
    dashboard_state.is_running = True
    logging_thread = threading.Thread(target=generate_synthetic_logs, daemon=True)
    logging_thread.start()
    logger.info("🚀 Synthetic log generation started")

def stop_synthetic_logging():
    """Stop synthetic log generation"""
    dashboard_state.is_running = False
    logger.info("🛑 Synthetic log generation stopped")

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
        'synthetic_logging': dashboard_state.is_running,
        'sre_agents_initialized': dashboard_state.rag_agent is not None
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
    
    if dashboard_state.rag_agent:
        agents.append({
            'name': 'RAG Agent',
            'status': 'online',
            'lastSeen': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
    if dashboard_state.mitigation_agent:
        agents.append({
            'name': 'Mitigation Agent',
            'status': 'online',
            'lastSeen': datetime.now().isoformat(),
            'version': '1.0.0'
        })
    
    # Add other agents
    agents.extend([
        {
            'name': 'Anomaly Detector',
            'status': 'online',
            'lastSeen': datetime.now().isoformat(),
            'version': '1.0.0'
        },
        {
            'name': 'Advanced LLM',
            'status': 'online',
            'lastSeen': datetime.now().isoformat(),
            'version': '1.0.0'
        },
        {
            'name': 'Paging Agent',
            'status': 'online',
            'lastSeen': datetime.now().isoformat(),
            'version': '1.0.0'
        }
    ])
    
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

@app.route('/api/anomaly-detection/status')
def get_anomaly_detection_status():
    """Get latest anomaly detection status"""
    if dashboard_state.last_detection_result:
        return jsonify(dashboard_state.last_detection_result)
    else:
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'is_anomaly': False,
            'confidence': 0.0,
            'reasoning': 'No detection results available',
            'service': 'unknown',
            'model_used': 'ML Model' if dashboard_state.ml_orchestrator and dashboard_state.ml_orchestrator.use_ml else 'Threshold Detection',
            'ml_explanation': None
        })

@app.route('/api/trigger-anomaly', methods=['POST'])
def trigger_anomaly():
    """Trigger a test anomaly"""
    try:
        data = request.get_json()
        anomaly_type = data.get('type', 'cpu_overload')
        
        # Create test log based on anomaly type
        test_log = create_test_anomaly_log(anomaly_type)
        
        # Add the anomaly log directly to recent logs
        log_entry_display = {
            'timestamp': test_log.get('timestamp', datetime.now().isoformat()),
            'service': test_log.get('service', 'unknown'),
            'level': test_log.get('level', 'INFO'),
            'message': test_log.get('message', ''),
            'anomaly': True,
            'request_id': test_log.get('request_id', 'unknown')
        }
        dashboard_state.recent_logs.insert(0, log_entry_display)
        dashboard_state.anomalies_detected += 1
        logger.info(f"✅ Added anomaly to recent logs: {test_log.get('request_id')}")
        
        # Try to process through SRE agents (but don't fail if it doesn't work)
        try:
            import asyncio
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(process_log_through_sre_agents(test_log))
            new_loop.close()
            logger.info(f"✅ Successfully processed anomaly {anomaly_type} through SRE agents")
        except Exception as e:
            logger.error(f"Error processing anomaly through SRE agents: {e}")
            # The log is already added above, so we don't need to do anything else
        
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
        dashboard_state.last_detection_result = None # Reset detection result
        
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

@app.route('/api/start-logging', methods=['POST'])
def start_logging():
    """Start synthetic log generation"""
    try:
        start_synthetic_logging()
        return jsonify({
            'success': True,
            'message': 'Synthetic log generation started'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stop-logging', methods=['POST'])
def stop_logging():
    """Stop synthetic log generation"""
    try:
        stop_synthetic_logging()
        return jsonify({
            'success': True,
            'message': 'Synthetic log generation stopped'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-report-generation', methods=['POST'])
def test_report_generation():
    """Test the report generation agent"""
    try:
        # Create test anomaly data
        test_anomaly = {
            'service': 'test-service',
            'request_id': 'test_report_001',
            'timestamp': datetime.now().isoformat(),
            'level': 'CRITICAL',
            'message': 'Test anomaly for report generation',
            'metrics': {
                'cpu_usage': 95.0,
                'memory_usage': 88.0,
                'error_rate': 0.15,
                'request_latency_ms': 8000,
                'active_connections': 1200
            }
        }
        
        # Create test LLM result
        test_llm_result = {
            'summary': 'Test critical issue requiring immediate attention.',
            'recommendations': [
                'Investigate the root cause immediately',
                'Scale up system resources',
                'Monitor system recovery'
            ],
            'priority': 'critical'
        }
        
        # Generate and send report
        if dashboard_state.report_agent:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                dashboard_state.report_agent.generate_and_send_report(test_anomaly, test_llm_result)
            )
            loop.close()
            
            return jsonify({
                'success': True,
                'message': 'Report generation test completed',
                'result': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Report agent not initialized'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error testing report generation: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/test-paging', methods=['POST'])
def test_paging():
    """Test the paging agent"""
    try:
        # Create test incident data
        test_incident = {
            'service': 'test-service',
            'request_id': 'test_paging_001',
            'timestamp': datetime.now().isoformat(),
            'level': 'CRITICAL',
            'message': 'Test incident for paging'
        }
        
        # Test paging
        if dashboard_state.paging_agent:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                dashboard_state.paging_agent.page_sre_oncall(test_incident)
            )
            loop.close()
            
            return jsonify({
                'success': True,
                'message': 'Paging test completed',
                'result': result
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Paging agent not initialized'
            }), 500
            
    except Exception as e:
        logger.error(f"❌ Error testing paging: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Starting Simplified SRE Agent Dashboard Server...")
    print(f"📊 Dashboard will be available at: http://localhost:{DASHBOARD_CONFIG['port']}")
    print(f"🔧 API endpoints available at: http://localhost:{DASHBOARD_CONFIG['port']}/api/")
    print(f"📁 Static files served from: {os.path.abspath('frontend')}")
    print(f"🐛 Debug mode: {DASHBOARD_CONFIG['debug']}")
    
    # Initialize SRE agents
    if initialize_sre_agents():
        print("✅ SRE Agent Components initialized successfully")
    else:
        print("⚠️  SRE Agent Components initialization failed")
    
    # Start synthetic logging
    start_synthetic_logging()
    print("✅ Synthetic log generation started")
    
    # Start Flask server
    app.run(
        host=DASHBOARD_CONFIG['host'],
        port=DASHBOARD_CONFIG['port'],
        debug=DASHBOARD_CONFIG['debug']
    ) 