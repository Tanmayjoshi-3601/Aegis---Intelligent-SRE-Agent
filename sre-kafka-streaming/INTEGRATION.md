# Kafka Log Streaming Pipeline Integration Guide

## Overview

This document provides a comprehensive guide for integrating the SRE Kafka Log Streaming Pipeline into your application and connecting it to an AI agent for real-time log analysis and anomaly detection.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│   Your App      │───▶│    Kafka     │───▶│  Log Consumer   │───▶│   AI Agent   │
│   (Log Source)  │    │   (Docker)   │    │   (Python)      │    │  (Analysis)  │
└─────────────────┘    └──────────────┘    └─────────────────┘    └──────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │   Monitor    │
                       │   (Python)   │
                       └──────────────┘
```

## Prerequisites

- Docker Desktop (v20.10+)
- Python 3.8+
- Kafka knowledge (basic)
- Your application that generates logs

## Quick Start Integration

### 1. Setup the Kafka Infrastructure

```bash
# Clone or copy the streaming pipeline
git clone <repository-url>
cd sre-kafka-streaming

# Start the infrastructure
./run_pipeline.sh

# Verify services are running
docker ps
```

### 2. Install Python Dependencies

```bash
pip install kafka-python
pip install openai  # For AI agent integration
pip install requests
```

## Integration Methods

### Method 1: Direct Kafka Producer Integration

#### Step 1: Add Kafka Producer to Your Application

```python
# kafka_integration.py
import json
import time
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError

class KafkaLogProducer:
    def __init__(self, bootstrap_servers='localhost:9092', topic='system-logs'):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.producer = None
        self.connect()
    
    def connect(self):
        """Connect to Kafka"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else b'',
                retries=3,
                acks='all'
            )
            print(f"✅ Connected to Kafka at {self.bootstrap_servers}")
        except Exception as e:
            print(f"❌ Failed to connect to Kafka: {e}")
            raise
    
    def send_log(self, log_data):
        """Send a log entry to Kafka"""
        try:
            # Add metadata
            log_data['timestamp'] = datetime.utcnow().isoformat()
            log_data['source'] = 'your-application'
            
            # Use service name as key for partitioning
            key = log_data.get('service', 'unknown')
            
            future = self.producer.send(
                self.topic,
                key=key,
                value=log_data
            )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            return True
            
        except Exception as e:
            print(f"❌ Error sending log: {e}")
            return False
    
    def send_batch(self, logs):
        """Send multiple logs in batch"""
        success_count = 0
        for log in logs:
            if self.send_log(log):
                success_count += 1
        
        # Flush to ensure all messages are sent
        self.producer.flush()
        return success_count
    
    def close(self):
        """Close the producer connection"""
        if self.producer:
            self.producer.close()
            print("✅ Kafka producer closed")

# Usage example
if __name__ == "__main__":
    producer = KafkaLogProducer()
    
    # Example log data
    sample_log = {
        "service": "user-service",
        "level": "INFO",
        "host": "user-service-1.prod.internal",
        "message": "User login successful",
        "metrics": {
            "cpu_usage": 45.2,
            "memory_usage": 52.1,
            "error_rate": 0.002,
            "request_latency_ms": 120,
            "active_connections": 50
        },
        "anomaly": False
    }
    
    # Send the log
    producer.send_log(sample_log)
    producer.close()
```

#### Step 2: Integrate with Your Application

```python
# your_application.py
import logging
from kafka_integration import KafkaLogProducer

class YourApplication:
    def __init__(self):
        self.kafka_producer = KafkaLogProducer()
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging to also send to Kafka"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def log_to_kafka(self, level, message, service="your-service", **kwargs):
        """Log to both standard logging and Kafka"""
        # Standard logging
        if level == "INFO":
            self.logger.info(message)
        elif level == "ERROR":
            self.logger.error(message)
        elif level == "WARNING":
            self.logger.warning(message)
        
        # Kafka logging
        log_data = {
            "service": service,
            "level": level,
            "message": message,
            "host": kwargs.get("host", "localhost"),
            "metrics": kwargs.get("metrics", {}),
            "anomaly": kwargs.get("anomaly", False),
            **kwargs
        }
        
        self.kafka_producer.send_log(log_data)
    
    def process_request(self, request_data):
        """Example application method"""
        try:
            # Your application logic here
            result = self.business_logic(request_data)
            
            # Log success
            self.log_to_kafka(
                "INFO", 
                f"Request processed successfully: {request_data['id']}",
                service="api-gateway",
                metrics={
                    "cpu_usage": 45.2,
                    "memory_usage": 52.1,
                    "error_rate": 0.002,
                    "request_latency_ms": 120
                }
            )
            
            return result
            
        except Exception as e:
            # Log error
            self.log_to_kafka(
                "ERROR", 
                f"Request failed: {str(e)}",
                service="api-gateway",
                metrics={
                    "cpu_usage": 85.2,
                    "memory_usage": 78.1,
                    "error_rate": 0.15,
                    "request_latency_ms": 850
                },
                anomaly=True
            )
            raise

# Usage
app = YourApplication()
app.process_request({"id": "123", "data": "test"})
```

### Method 2: HTTP API Integration

#### Step 1: Create a Log Ingestion API

```python
# log_api.py
from flask import Flask, request, jsonify
from kafka_integration import KafkaLogProducer
import threading
import time

app = Flask(__name__)
kafka_producer = KafkaLogProducer()

@app.route('/api/logs', methods=['POST'])
def ingest_log():
    """Ingest log via HTTP API"""
    try:
        log_data = request.json
        
        # Validate required fields
        required_fields = ['service', 'level', 'message']
        for field in required_fields:
            if field not in log_data:
                return jsonify({"error": f"Missing required field: {field}"}), 400
        
        # Send to Kafka
        success = kafka_producer.send_log(log_data)
        
        if success:
            return jsonify({"status": "success", "message": "Log ingested successfully"}), 200
        else:
            return jsonify({"error": "Failed to send log to Kafka"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/logs/batch', methods=['POST'])
def ingest_logs_batch():
    """Ingest multiple logs via HTTP API"""
    try:
        logs = request.json.get('logs', [])
        
        if not logs:
            return jsonify({"error": "No logs provided"}), 400
        
        success_count = kafka_producer.send_batch(logs)
        
        return jsonify({
            "status": "success", 
            "message": f"Processed {success_count}/{len(logs)} logs"
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

#### Step 2: Send Logs from Your Application

```python
# your_app_with_api.py
import requests
import json

class LogClient:
    def __init__(self, api_url='http://localhost:5000'):
        self.api_url = api_url
    
    def send_log(self, log_data):
        """Send log via HTTP API"""
        try:
            response = requests.post(
                f"{self.api_url}/api/logs",
                json=log_data,
                headers={'Content-Type': 'application/json'}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending log: {e}")
            return False
    
    def send_batch(self, logs):
        """Send multiple logs via HTTP API"""
        try:
            response = requests.post(
                f"{self.api_url}/api/logs/batch",
                json={'logs': logs},
                headers={'Content-Type': 'application/json'}
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Error sending batch: {e}")
            return False

# Usage
log_client = LogClient()
log_client.send_log({
    "service": "user-service",
    "level": "INFO",
    "message": "User login successful",
    "metrics": {
        "cpu_usage": 45.2,
        "memory_usage": 52.1,
        "error_rate": 0.002
    }
})
```

## AI Agent Integration

### Step 1: Create AI Agent Consumer

```python
# ai_agent_consumer.py
import json
import time
from datetime import datetime
from kafka import KafkaConsumer
from kafka.errors import KafkaError
import openai
import os

class AIAgentConsumer:
    def __init__(self, bootstrap_servers='localhost:9092', topic='system-logs'):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.consumer = None
        self.openai_client = None
        self.setup_ai()
        self.connect()
    
    def setup_ai(self):
        """Setup OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("⚠️ OPENAI_API_KEY not set. AI analysis will be disabled.")
            return
        
        self.openai_client = openai.OpenAI(api_key=api_key)
        print("✅ OpenAI client configured")
    
    def connect(self):
        """Connect to Kafka as consumer"""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='ai-agent-consumer',
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            print("✅ AI Agent connected to Kafka")
        except Exception as e:
            print(f"❌ Failed to connect AI Agent: {e}")
            raise
    
    def analyze_log_with_ai(self, log_data):
        """Analyze log using AI"""
        if not self.openai_client:
            return {"analysis": "AI not configured", "recommendations": []}
        
        try:
            # Prepare context for AI
            context = f"""
            Analyze this system log for potential issues and provide recommendations:
            
            Service: {log_data.get('service', 'unknown')}
            Level: {log_data.get('level', 'unknown')}
            Message: {log_data.get('message', '')}
            Metrics: {json.dumps(log_data.get('metrics', {}), indent=2)}
            Anomaly Flag: {log_data.get('anomaly', False)}
            Timestamp: {log_data.get('timestamp', '')}
            
            Please provide:
            1. Issue analysis
            2. Severity assessment
            3. Immediate actions
            4. Long-term recommendations
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an SRE expert analyzing system logs for issues and providing actionable recommendations."},
                    {"role": "user", "content": context}
                ],
                max_tokens=500
            )
            
            return {
                "analysis": response.choices[0].message.content,
                "timestamp": datetime.utcnow().isoformat(),
                "log_id": log_data.get('id', 'unknown')
            }
            
        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            return {"analysis": f"AI analysis failed: {e}", "recommendations": []}
    
    def process_log(self, log_data):
        """Process a single log entry"""
        print(f"📊 Processing log from {log_data.get('service', 'unknown')}")
        
        # Check if this is an anomaly
        if log_data.get('anomaly', False):
            print(f"🚨 ANOMALY DETECTED: {log_data.get('service')}")
            
            # Get AI analysis
            ai_analysis = self.analyze_log_with_ai(log_data)
            
            # Store or forward the analysis
            self.store_analysis(log_data, ai_analysis)
            
            # Trigger alerts
            self.trigger_alert(log_data, ai_analysis)
    
    def store_analysis(self, log_data, analysis):
        """Store AI analysis (implement based on your needs)"""
        # This could store to database, send to another service, etc.
        analysis_data = {
            "log": log_data,
            "ai_analysis": analysis,
            "processed_at": datetime.utcnow().isoformat()
        }
        
        # Example: Store to file
        with open("ai_analysis.jsonl", "a") as f:
            f.write(json.dumps(analysis_data) + "\n")
    
    def trigger_alert(self, log_data, analysis):
        """Trigger alert based on AI analysis"""
        # Implement your alerting logic here
        # Could send to Slack, email, PagerDuty, etc.
        alert = {
            "service": log_data.get('service'),
            "severity": "high" if log_data.get('anomaly') else "medium",
            "message": log_data.get('message'),
            "ai_analysis": analysis,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        print(f"🔔 ALERT: {alert}")
        # Send alert to your preferred system
    
    def start_consuming(self):
        """Start consuming logs from Kafka"""
        print("🤖 AI Agent starting to consume logs...")
        
        try:
            for message in self.consumer:
                log_data = message.value
                self.process_log(log_data)
                
        except KeyboardInterrupt:
            print("🤖 AI Agent stopped by user")
        except Exception as e:
            print(f"❌ AI Agent error: {e}")
        finally:
            self.close()
    
    def close(self):
        """Close the consumer connection"""
        if self.consumer:
            self.consumer.close()
            print("✅ AI Agent connection closed")

# Usage
if __name__ == "__main__":
    ai_agent = AIAgentConsumer()
    ai_agent.start_consuming()
```

### Step 2: Enhanced AI Agent with Real-time Monitoring

```python
# enhanced_ai_agent.py
import json
import time
from datetime import datetime, timedelta
from kafka import KafkaConsumer
from collections import defaultdict, deque
import openai
import os

class EnhancedAIAgent:
    def __init__(self, bootstrap_servers='localhost:9092', topic='system-logs'):
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        self.consumer = None
        self.openai_client = None
        self.service_metrics = defaultdict(lambda: {
            'logs': deque(maxlen=100),
            'anomalies': deque(maxlen=50),
            'last_analysis': None
        })
        self.setup_ai()
        self.connect()
    
    def setup_ai(self):
        """Setup OpenAI client"""
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.openai_client = openai.OpenAI(api_key=api_key)
            print("✅ OpenAI client configured")
        else:
            print("⚠️ OPENAI_API_KEY not set. Using mock analysis.")
    
    def connect(self):
        """Connect to Kafka"""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='enhanced-ai-agent',
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            print("✅ Enhanced AI Agent connected to Kafka")
        except Exception as e:
            print(f"❌ Failed to connect: {e}")
            raise
    
    def get_service_context(self, service):
        """Get historical context for a service"""
        metrics = self.service_metrics[service]
        
        if not metrics['logs']:
            return "No historical data available"
        
        recent_logs = list(metrics['logs'])[-10:]  # Last 10 logs
        anomaly_count = len(metrics['anomalies'])
        
        context = f"""
        Service: {service}
        Recent logs: {len(recent_logs)}
        Recent anomalies: {anomaly_count}
        Last analysis: {metrics['last_analysis'] or 'None'}
        
        Recent log levels: {[log.get('level') for log in recent_logs]}
        Recent error rates: {[log.get('metrics', {}).get('error_rate', 0) for log in recent_logs]}
        """
        
        return context
    
    def analyze_service_health(self, service):
        """Analyze overall service health"""
        if not self.openai_client:
            return self.mock_analysis(service)
        
        try:
            context = self.get_service_context(service)
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an SRE expert analyzing service health patterns."},
                    {"role": "user", "content": f"Analyze the health of this service:\n{context}"}
                ],
                max_tokens=300
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"❌ AI analysis failed: {e}")
            return self.mock_analysis(service)
    
    def mock_analysis(self, service):
        """Mock analysis when AI is not available"""
        metrics = self.service_metrics[service]
        anomaly_count = len(metrics['anomalies'])
        
        if anomaly_count > 5:
            return f"⚠️ {service} shows concerning patterns with {anomaly_count} recent anomalies"
        elif anomaly_count > 0:
            return f"📊 {service} has {anomaly_count} anomalies but appears stable"
        else:
            return f"✅ {service} appears healthy with no recent anomalies"
    
    def process_log(self, log_data):
        """Process log with enhanced analysis"""
        service = log_data.get('service', 'unknown')
        
        # Store log in service metrics
        self.service_metrics[service]['logs'].append(log_data)
        
        # Check for anomaly
        if log_data.get('anomaly', False):
            self.service_metrics[service]['anomalies'].append(log_data)
            print(f"🚨 ANOMALY: {service} - {log_data.get('message', '')}")
            
            # Analyze service health
            analysis = self.analyze_service_health(service)
            self.service_metrics[service]['last_analysis'] = analysis
            
            print(f"🤖 AI Analysis: {analysis}")
            
            # Trigger intelligent alert
            self.trigger_intelligent_alert(service, log_data, analysis)
    
    def trigger_intelligent_alert(self, service, log_data, analysis):
        """Trigger intelligent alert based on AI analysis"""
        alert = {
            "service": service,
            "severity": self.calculate_severity(service),
            "message": log_data.get('message'),
            "ai_analysis": analysis,
            "metrics": log_data.get('metrics', {}),
            "timestamp": datetime.utcnow().isoformat(),
            "recommended_actions": self.get_recommended_actions(service, log_data)
        }
        
        print(f"🔔 INTELLIGENT ALERT: {json.dumps(alert, indent=2)}")
    
    def calculate_severity(self, service):
        """Calculate alert severity based on service patterns"""
        metrics = self.service_metrics[service]
        anomaly_count = len(metrics['anomalies'])
        
        if anomaly_count > 10:
            return "critical"
        elif anomaly_count > 5:
            return "high"
        elif anomaly_count > 0:
            return "medium"
        else:
            return "low"
    
    def get_recommended_actions(self, service, log_data):
        """Get recommended actions based on log data"""
        metrics = log_data.get('metrics', {})
        actions = []
        
        if metrics.get('cpu_usage', 0) > 85:
            actions.append("Scale up CPU resources")
        if metrics.get('memory_usage', 0) > 85:
            actions.append("Increase memory allocation")
        if metrics.get('error_rate', 0) > 0.05:
            actions.append("Investigate error patterns")
        if metrics.get('active_connections', 0) > 450:
            actions.append("Increase connection pool size")
        
        return actions
    
    def start_consuming(self):
        """Start consuming logs"""
        print("🤖 Enhanced AI Agent starting...")
        
        try:
            for message in self.consumer:
                log_data = message.value
                self.process_log(log_data)
                
        except KeyboardInterrupt:
            print("🤖 Enhanced AI Agent stopped")
        except Exception as e:
            print(f"❌ Enhanced AI Agent error: {e}")
        finally:
            self.close()
    
    def close(self):
        """Close connection"""
        if self.consumer:
            self.consumer.close()
            print("✅ Enhanced AI Agent closed")

# Usage
if __name__ == "__main__":
    agent = EnhancedAIAgent()
    agent.start_consuming()
```

## Configuration

### Environment Variables

```bash
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=system-logs

# AI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Application Configuration
LOG_API_URL=http://localhost:5000
LOG_LEVEL=INFO
```

### Docker Compose Integration

Add to your `docker-compose.yml`:

```yaml
services:
  # Your existing services...
  
  log-api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:29092
      - KAFKA_TOPIC=system-logs
    depends_on:
      - kafka
    networks:
      - sre-network
  
  ai-agent:
    build: .
    environment:
      - KAFKA_BOOTSTRAP_SERVERS=kafka:29092
      - KAFKA_TOPIC=system-logs
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - kafka
    networks:
      - sre-network
```

## Log Format Specification

### Required Fields

```json
{
  "service": "string",           // Service name (required)
  "level": "string",             // Log level: INFO, WARN, ERROR (required)
  "message": "string",           // Log message (required)
  "timestamp": "string",         // ISO 8601 timestamp
  "host": "string",              // Host identifier
  "metrics": {                   // Optional metrics
    "cpu_usage": 45.2,           // CPU usage percentage
    "memory_usage": 52.1,        // Memory usage percentage
    "error_rate": 0.002,         // Error rate (0-1)
    "request_latency_ms": 120,   // Request latency in ms
    "active_connections": 50     // Active connections
  },
  "anomaly": false,              // Anomaly flag
  "source": "string",            // Source application
  "user_id": "string",           // User identifier (if applicable)
  "request_id": "string",        // Request identifier (if applicable)
  "tags": ["tag1", "tag2"]       // Custom tags
}
```

### Example Log Entry

```json
{
  "service": "user-service",
  "level": "ERROR",
  "message": "Database connection timeout",
  "timestamp": "2025-08-12T18:30:00.000Z",
  "host": "user-service-1.prod.internal",
  "metrics": {
    "cpu_usage": 85.2,
    "memory_usage": 78.1,
    "error_rate": 0.15,
    "request_latency_ms": 850,
    "active_connections": 480
  },
  "anomaly": true,
  "source": "your-application",
  "request_id": "req-12345",
  "tags": ["database", "timeout", "critical"]
}
```

## Testing the Integration

### 1. Test Kafka Connection

```python
# test_kafka_connection.py
from kafka_integration import KafkaLogProducer

def test_connection():
    producer = KafkaLogProducer()
    
    test_log = {
        "service": "test-service",
        "level": "INFO",
        "message": "Test log message",
        "metrics": {
            "cpu_usage": 45.2,
            "memory_usage": 52.1,
            "error_rate": 0.002
        }
    }
    
    success = producer.send_log(test_log)
    print(f"Test log sent: {success}")
    producer.close()

if __name__ == "__main__":
    test_connection()
```

### 2. Test AI Agent

```python
# test_ai_agent.py
from ai_agent_consumer import AIAgentConsumer
import time

def test_ai_agent():
    agent = AIAgentConsumer()
    
    # Test with sample log
    test_log = {
        "service": "test-service",
        "level": "ERROR",
        "message": "Test error message",
        "metrics": {
            "cpu_usage": 95.2,
            "memory_usage": 88.1,
            "error_rate": 0.25
        },
        "anomaly": True
    }
    
    analysis = agent.analyze_log_with_ai(test_log)
    print(f"AI Analysis: {analysis}")
    agent.close()

if __name__ == "__main__":
    test_ai_agent()
```

## Monitoring and Alerting

### 1. Health Checks

```python
# health_check.py
import requests
import json

def check_kafka_health():
    """Check Kafka connectivity"""
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(bootstrap_servers='localhost:9092')
        producer.close()
        return True
    except Exception as e:
        print(f"Kafka health check failed: {e}")
        return False

def check_ai_agent_health():
    """Check AI agent health"""
    try:
        # Check if AI agent is processing logs
        # This could check a health endpoint or log file
        return True
    except Exception as e:
        print(f"AI agent health check failed: {e}")
        return False

def run_health_checks():
    """Run all health checks"""
    checks = {
        "kafka": check_kafka_health(),
        "ai_agent": check_ai_agent_health()
    }
    
    all_healthy = all(checks.values())
    print(f"Health check results: {checks}")
    return all_healthy

if __name__ == "__main__":
    run_health_checks()
```

### 2. Metrics Collection

```python
# metrics_collector.py
import time
from datetime import datetime
from kafka import KafkaConsumer
import json

class MetricsCollector:
    def __init__(self):
        self.consumer = KafkaConsumer(
            'system-logs',
            bootstrap_servers='localhost:9092',
            auto_offset_reset='latest',
            group_id='metrics-collector'
        )
        self.metrics = {
            'total_logs': 0,
            'anomalies': 0,
            'services': {},
            'hourly_stats': {}
        }
    
    def collect_metrics(self):
        """Collect metrics from Kafka logs"""
        print("📊 Starting metrics collection...")
        
        try:
            for message in self.consumer:
                log = message.value
                self.process_log_for_metrics(log)
                
                # Print metrics every 100 logs
                if self.metrics['total_logs'] % 100 == 0:
                    self.print_metrics()
                    
        except KeyboardInterrupt:
            print("📊 Metrics collection stopped")
            self.print_final_metrics()
    
    def process_log_for_metrics(self, log):
        """Process log for metrics collection"""
        self.metrics['total_logs'] += 1
        
        if log.get('anomaly', False):
            self.metrics['anomalies'] += 1
        
        service = log.get('service', 'unknown')
        if service not in self.metrics['services']:
            self.metrics['services'][service] = {
                'total_logs': 0,
                'anomalies': 0,
                'error_count': 0
            }
        
        self.metrics['services'][service]['total_logs'] += 1
        
        if log.get('anomaly', False):
            self.metrics['services'][service]['anomalies'] += 1
        
        if log.get('level') == 'ERROR':
            self.metrics['services'][service]['error_count'] += 1
    
    def print_metrics(self):
        """Print current metrics"""
        print(f"\n📊 Current Metrics:")
        print(f"Total Logs: {self.metrics['total_logs']}")
        print(f"Anomalies: {self.metrics['anomalies']}")
        print(f"Anomaly Rate: {self.metrics['anomalies']/max(self.metrics['total_logs'], 1)*100:.2f}%")
        print(f"Services: {len(self.metrics['services'])}")
    
    def print_final_metrics(self):
        """Print final metrics summary"""
        print(f"\n📊 Final Metrics Summary:")
        print(json.dumps(self.metrics, indent=2))

# Usage
if __name__ == "__main__":
    collector = MetricsCollector()
    collector.collect_metrics()
```

## Troubleshooting

### Common Issues

1. **Kafka Connection Failed**
   ```bash
   # Check if Kafka is running
   docker ps | grep kafka
   
   # Check Kafka logs
   docker logs sre-kafka
   
   # Test connectivity
   nc -z localhost 9092
   ```

2. **AI Agent Not Responding**
   ```bash
   # Check OpenAI API key
   echo $OPENAI_API_KEY
   
   # Test OpenAI connection
   python -c "import openai; openai.api_key='your_key'; print('OK')"
   ```

3. **High Memory Usage**
   ```bash
   # Check memory usage
   docker stats
   
   # Restart services
   docker-compose restart
   ```

### Debug Commands

```bash
# Check all services
./debug_commands.sh all

# Check Kafka topics
docker exec sre-kafka kafka-topics --list --bootstrap-server localhost:9092

# Check consumer groups
docker exec sre-kafka kafka-consumer-groups --list --bootstrap-server localhost:9092

# View recent messages
docker exec sre-kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic system-logs --from-beginning --max-messages 10
```

## Performance Optimization

### 1. Batch Processing

```python
# batch_processor.py
import time
from kafka_integration import KafkaLogProducer

class BatchProcessor:
    def __init__(self, batch_size=100, flush_interval=5):
        self.producer = KafkaLogProducer()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.batch = []
        self.last_flush = time.time()
    
    def add_log(self, log_data):
        """Add log to batch"""
        self.batch.append(log_data)
        
        # Flush if batch is full or time interval reached
        if (len(self.batch) >= self.batch_size or 
            time.time() - self.last_flush >= self.flush_interval):
            self.flush()
    
    def flush(self):
        """Flush batch to Kafka"""
        if self.batch:
            success_count = self.producer.send_batch(self.batch)
            print(f"📦 Flushed {success_count}/{len(self.batch)} logs")
            self.batch = []
            self.last_flush = time.time()
    
    def close(self):
        """Close processor"""
        self.flush()
        self.producer.close()

# Usage
processor = BatchProcessor()
for i in range(1000):
    processor.add_log({
        "service": "batch-service",
        "level": "INFO",
        "message": f"Batch log {i}"
    })
processor.close()
```

### 2. Connection Pooling

```python
# connection_pool.py
from kafka import KafkaProducer
import threading
import time

class KafkaConnectionPool:
    def __init__(self, bootstrap_servers='localhost:9092', pool_size=5):
        self.bootstrap_servers = bootstrap_servers
        self.pool_size = pool_size
        self.producers = []
        self.lock = threading.Lock()
        self.init_pool()
    
    def init_pool(self):
        """Initialize connection pool"""
        for _ in range(self.pool_size):
            producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            self.producers.append(producer)
    
    def get_producer(self):
        """Get producer from pool"""
        with self.lock:
            if self.producers:
                return self.producers.pop()
            else:
                # Create new producer if pool is empty
                return KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
    
    def return_producer(self, producer):
        """Return producer to pool"""
        with self.lock:
            if len(self.producers) < self.pool_size:
                self.producers.append(producer)
            else:
                producer.close()
    
    def close_all(self):
        """Close all producers"""
        with self.lock:
            for producer in self.producers:
                producer.close()
            self.producers.clear()
```

## Security Considerations

### 1. Authentication

```python
# secure_kafka_producer.py
from kafka import KafkaProducer
import ssl

class SecureKafkaProducer:
    def __init__(self, bootstrap_servers='localhost:9092', 
                 username=None, password=None, 
                 ssl_cafile=None, ssl_certfile=None, ssl_keyfile=None):
        
        security_config = {}
        
        if username and password:
            security_config['security_protocol'] = 'SASL_SSL'
            security_config['sasl_mechanism'] = 'PLAIN'
            security_config['sasl_plain_username'] = username
            security_config['sasl_plain_password'] = password
        
        if ssl_cafile:
            security_config['ssl_cafile'] = ssl_cafile
        if ssl_certfile:
            security_config['ssl_certfile'] = ssl_certfile
        if ssl_keyfile:
            security_config['ssl_keyfile'] = ssl_keyfile
        
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            **security_config
        )
```

### 2. Data Encryption

```python
# encrypted_log_processor.py
import base64
from cryptography.fernet import Fernet

class EncryptedLogProcessor:
    def __init__(self, encryption_key=None):
        if encryption_key:
            self.cipher = Fernet(encryption_key)
        else:
            self.cipher = Fernet(Fernet.generate_key())
    
    def encrypt_log(self, log_data):
        """Encrypt log data"""
        log_str = json.dumps(log_data)
        encrypted = self.cipher.encrypt(log_str.encode())
        return base64.b64encode(encrypted).decode()
    
    def decrypt_log(self, encrypted_data):
        """Decrypt log data"""
        encrypted = base64.b64decode(encrypted_data.encode())
        decrypted = self.cipher.decrypt(encrypted)
        return json.loads(decrypted.decode())
```

## Deployment Checklist

- [ ] Kafka infrastructure running
- [ ] Python dependencies installed
- [ ] Environment variables configured
- [ ] Log format standardized
- [ ] AI agent configured
- [ ] Health checks implemented
- [ ] Monitoring setup
- [ ] Security measures in place
- [ ] Performance testing completed
- [ ] Documentation updated

## Support

For issues and questions:

1. Check the troubleshooting section
2. Run `./debug_commands.sh all`
3. Check Docker logs: `docker-compose logs -f [service-name]`
4. Review the integration examples above

## Next Steps

1. **Customize the log format** for your application
2. **Implement your AI agent** logic
3. **Add your specific alerting** mechanisms
4. **Scale the infrastructure** as needed
5. **Monitor and optimize** performance

Happy integrating! 🚀 