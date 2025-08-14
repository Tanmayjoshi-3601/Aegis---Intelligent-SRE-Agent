# 🛡️ Aegis - Intelligent SRE Agent

A comprehensive Site Reliability Engineering (SRE) system that combines Machine Learning anomaly detection, RAG-based knowledge retrieval, and automated mitigation strategies with real-time monitoring and human escalation capabilities.

![SRE Dashboard](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![ML](https://img.shields.io/badge/ML-Scikit--learn-orange)
![Kafka](https://img.shields.io/badge/Kafka-Streaming-red)
![Twilio](https://img.shields.io/badge/Twilio-Paging-blue)
![SendGrid](https://img.shields.io/badge/SendGrid-Email-green)

## 🎯 Overview

Aegis is an intelligent SRE agent that provides end-to-end automation for detecting, analyzing, and resolving system anomalies in real-time. It combines multiple AI agents working in orchestration to provide intelligent, automated incident response with human oversight for critical issues.

### 🔥 Key Features

#### 🤖 **Multi-Agent Architecture**
- **Anomaly Detection Agent**: ML-powered real-time anomaly detection using trained models
- **RAG Agent**: Retrieval-Augmented Generation for intelligent knowledge base queries
- **Mitigation Agent**: Automated execution and validation of remediation actions
- **Critical Anomaly Reasoning Agent**: Advanced LLM analysis for complex issues
- **Report Generation Agent**: Automated incident report creation and email delivery
- **Paging Agent**: Human escalation via Twilio phone calls

#### 🧠 **Intelligent Processing**
- **Real-time ML Inference**: Continuous anomaly detection using trained models
- **RAG Knowledge Base**: Pre-defined playbooks for common SRE scenarios
- **Validation Simulator**: Risk-free testing of mitigation actions before execution
- **Metrics Tracking**: Comprehensive before/after analysis of all actions
- **Confidence Scoring**: AI-driven confidence levels for all decisions

#### 📊 **Real-Time Dashboard**
- **Live Log Streaming**: Real-time visualization of system logs
- **Agent Activity Monitoring**: Live status of all SRE agents
- **Anomaly Visualization**: Color-coded log streams (green=normal, red=anomaly)
- **Reasoning Trace**: Step-by-step agent decision process visualization
- **Metrics Graphs**: Real-time system performance metrics
- **Interactive Controls**: Manual anomaly injection for testing

#### 🔧 **Automated Mitigation**
- **Service Restart**: Automatic service recovery
- **Horizontal Scaling**: Load distribution across instances
- **Cache Management**: Memory optimization strategies
- **Connection Pool Management**: Database connection optimization
- **Circuit Breaker**: Fault tolerance implementation
- **Request Throttling**: Rate limiting for overload protection

#### 🚨 **Human Escalation**
- **Critical Issue Detection**: Automatic identification of severe anomalies
- **Email Reports**: Detailed incident reports via SendGrid
- **Phone Paging**: Immediate human notification via Twilio
- **Escalation Workflow**: Automated routing to appropriate teams

## 🏗️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Kafka Stream  │───▶│  ML Orchestrator│───▶│ Anomaly Detector│
│   (Log Input)   │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   RAG Agent     │◀───│  Orchestrator   │───▶│ Mitigation Agent│
│ (Knowledge Base)│    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Critical LLM    │    │ Report Gen.     │    │ Paging Agent    │
│ Agent           │    │ Agent           │    │ (Twilio)        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔐 Environment Variables

This project uses environment variables to manage sensitive configuration like API keys and credentials. 

### Setup Instructions

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file with your actual credentials:**
   ```bash
   # OpenAI API Configuration
   OPENAI_API_KEY=your-actual-openai-api-key
   
   # Twilio Configuration (for phone paging)
   TWILIO_ACCOUNT_SID=your-twilio-account-sid
   TWILIO_AUTH_TOKEN=your-twilio-auth-token
   TWILIO_FROM_NUMBER=your-twilio-from-number
   SRE_ONCALL_PHONE=your-oncall-phone-number
   
   # SendGrid Configuration (for email reports)
   SENDGRID_API_KEY=your-sendgrid-api-key
   SRE_SENDER_EMAIL=your-sender-email
   SRE_RECIPIENT_EMAIL=your-recipient-email
   
   # Database Configuration
   POSTGRES_PASSWORD=your-postgres-password
   ```

3. **Important:** The `.env` file is ignored by git to keep your secrets safe. Never commit your actual API keys!

### Required Services

- **OpenAI API**: For LLM-powered analysis and recommendations
- **Twilio**: For phone call notifications (optional)
- **SendGrid**: For email report delivery (optional)
- **PostgreSQL**: For data persistence (optional)

## 📁 Project Structure

```
Aegis---Intelligent-SRE-Agent/
├── orchestration/          # Core orchestration engine
│   ├── ml_orchestrator.py  # ML model orchestration
│   ├── sre_agent_orchestrator.py  # Main SRE orchestrator
│   ├── validation_simulator.py    # Mitigation validation
│   └── config.py           # Orchestration configuration
├── agents/                 # Individual agent implementations
│   ├── anomaly_detector_agent.py  # ML-based anomaly detection
│   ├── rag_agent.py        # RAG knowledge retrieval
│   ├── mitigation_agent.py # Automated mitigation
│   ├── advanced_llm_agent.py      # Critical issue analysis
│   ├── report_generation_agent.py # Email report generation
│   ├── paging_agent.py     # Twilio phone paging
│   └── __init__.py         # Agent package initialization
├── ml_pipeline/            # ML models and training
│   ├── anomaly_detector.py # ML pipeline for anomaly detection
│   ├── saved_models/       # Trained model files
│   └── notebooks/          # Jupyter notebooks for exploration
├── streaming/              # Kafka integration
│   └── kafka/              # Kafka streaming components
│       └── custom_log_streamer.py
├── communications/         # Voice and email systems
│   ├── eleven_labs/        # Voice synthesis (future)
│   └── twilio/             # Call and email delivery (future)
├── frontend/               # Dashboard UI
│   ├── index.html          # Main dashboard
│   ├── styles.css          # Dashboard styling
│   └── js/                 # JavaScript components
├── data/                   # Synthetic data and knowledge base
│   ├── knowledge_base/     # RAG knowledge base
│   ├── logs.json           # Sample log data
│   ├── metadata.json       # System metadata
│   └── playbooks/          # Mitigation playbooks
├── tests/                  # Test suites
│   ├── test_complete_system.py
│   ├── test_ml_orchestrator.py
│   ├── test_rag_agent.py
│   └── test_streaming.py
├── config/                 # Configuration files
│   └── sre_agent_config.json
├── scripts/                # Setup and utility scripts
│   ├── init_db.sql         # Database initialization
│   ├── install.sh          # Installation script
│   └── cleanup.sh          # Cleanup utilities
├── logs/                   # Application logs
├── docs/                   # Documentation
│   ├── README_DASHBOARD.md
│   ├── README_SRE_AGENT.md
│   ├── KAFKA_SETUP_GUIDE.md
│   └── INTEGRATION.md
├── config/docker-compose.yml      # Infrastructure setup
├── config/requirements.txt        # Python dependencies
├── config/requirements-dashboard.txt
├── config/requirements-streaming.txt
├── orchestration/config.py        # Main configuration
├── orchestration/dashboard_server.py     # Dashboard server
├── orchestration/dashboard_server_simple.py
├── scripts/start_dashboard.sh      # Dashboard startup script
├── scripts/start_sre_agent.sh      # SRE agent startup script
├── scripts/start_streaming.sh      # Streaming startup script
└── README.md                       # This file
```

## 📋 Prerequisites

- **Python 3.8+**
- **Docker & Docker Compose** (for Kafka infrastructure)
- **OpenAI API Key** (for RAG and LLM agents)
- **Twilio Account** (for paging functionality)
- **SendGrid Account** (for email reports)
- **8GB+ RAM** (for ML model inference)
- **macOS/Linux** (tested on macOS 22.6.0)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd Aegis---Intelligent-SRE-Agent
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r config/requirements.txt
pip install -r config/requirements-dashboard.txt
pip install -r config/requirements-streaming.txt

# Or use the automated installer
chmod +x scripts/install.sh
./scripts/install.sh
```

### 3. Configure API Keys

Create a `orchestration/config.py` file with your API credentials:

```python
# OpenAI Configuration
OPENAI_CONFIG = {
    'api_key': 'your-openai-api-key-here',
    'model': 'gpt-4',
    'temperature': 0.1
}

# Twilio Configuration (for paging)
TWILIO_CONFIG = {
    'account_sid': 'your-twilio-account-sid',
    'auth_token': 'your-twilio-auth-token',
    'from_number': '+1234567890',
    'to_number': '+1987654321'
}

# SendGrid Configuration (for email reports)
SENDGRID_CONFIG = {
    'api_key': 'your-sendgrid-api-key',
    'from_email': 'sre-alerts@yourcompany.com',
    'to_email': 'oncall@yourcompany.com'
}
```

### 4. Generate Synthetic Data and Train Models

```bash
# Generate training data
python orchestration/synthetic_data_generator.py --training

# Generate streaming data
python orchestration/synthetic_data_generator.py --streaming

# Train ML models
python ml_pipeline/anomaly_detector.py --train
```

### 5. Start Infrastructure

```bash
# Start Kafka, Zookeeper, Redis, and PostgreSQL
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
sleep 30
```

### 6. Start the SRE Dashboard

```bash
# Start the dashboard server
python3 orchestration/dashboard_server_simple.py

# Or use the automated startup script
chmod +x scripts/start_dashboard.sh
./scripts/start_dashboard.sh
```

### 7. Access the Dashboard

Open your browser and navigate to:
```
http://localhost:8082
```

## 🎮 Usage Guide

### Dashboard Interface

The dashboard provides several key sections:

#### 📊 **Live Metrics Panel**
- Real-time system performance metrics
- CPU, Memory, Error Rate, Latency monitoring
- Historical trend visualization

#### 🔍 **Agent Status Panel**
- Live status of all SRE agents
- Current activity and processing state
- Agent confidence levels and decisions

#### 📝 **Live Log Stream**
- Real-time log visualization
- Color-coded by severity (green=normal, red=anomaly)
- Automatic anomaly highlighting

#### 🧠 **Reasoning Trace**
- Step-by-step agent decision process
- Real-time reasoning updates
- Agent thought process visualization

#### 🎯 **Anomaly Injection Panel**
- Manual anomaly injection for testing
- Pre-defined anomaly scenarios:
  - **CPU Overload**: High CPU usage simulation
  - **Memory Leak**: Memory exhaustion scenario
  - **Service Crash**: Critical service failure
  - **Database Issues**: Connection pool exhaustion
  - **Network Latency**: High latency simulation

### Testing the System

#### 1. **Normal Operation**
- Watch the dashboard during normal operation
- Observe green logs and "Anomaly Not Detected" status
- Monitor agent activity and reasoning trace

#### 2. **Inject Anomaly**
- Click on any anomaly preset button
- Observe the complete flow:
  1. **Anomaly Detector** (5s): ML inference and detection
  2. **RAG Agent** (5s): Knowledge base analysis
  3. **Mitigation Agent** (10s): Automated resolution
  4. **Critical Path** (if applicable): LLM analysis + Paging

#### 3. **Critical Issue Testing**
- Inject "Service Crash" anomaly
- Observe escalation to Critical Anomaly Reasoning Agent
- Watch email report generation and phone paging

### Streaming Integration

#### Basic Streaming

```bash
# Start Kafka infrastructure
./scripts/start_streaming.sh start

# Stream your application logs
python orchestration/stream_logs_direct.py
```

#### High-Volume Streaming

```bash
# Stream at higher rates using the integration service
python orchestration/streaming_integration.py --mode normal --rate 10 --duration 60 --kafka-servers 127.0.0.1:9093
```

#### Burst Mode (Simulate High Load)

```bash
# Stream in bursts to simulate traffic spikes
python orchestration/streaming_integration.py --mode burst --rate 20 --duration 30 --kafka-servers 127.0.0.1:9093
```

## 🔧 Configuration

### Environment Variables

```bash
export OPENAI_API_KEY="your-openai-key"
export TWILIO_ACCOUNT_SID="your-twilio-sid"
export TWILIO_AUTH_TOKEN="your-twilio-token"
export SENDGRID_API_KEY="your-sendgrid-key"
```

### Kafka Configuration

The system uses Kafka for log streaming. Default configuration:

```yaml
# docker-compose.yml
kafka:
  ports:
    - "9092:9092"  # Kafka broker
  environment:
    KAFKA_NUM_PARTITIONS: 3
    KAFKA_LOG_RETENTION_HOURS: 24
```

### ML Model Configuration

```python
# config.py
ML_CONFIG = {
    'model_path': 'ml_pipeline/saved_models/',
    'anomaly_threshold': 0.7,
    'batch_size': 100,
    'update_interval': 30
}
```

## 🧪 Testing

### Run Complete System Test

```bash
python3 tests/test_complete_system.py
```

### Test Individual Components

```bash
# Test ML Orchestrator
python3 tests/test_ml_orchestrator.py

# Test RAG Agent
python3 tests/test_rag_agent.py

# Test Mitigation Agent
python3 tests/test_streaming.py
```

### Manual Testing via Dashboard

1. **Start the dashboard**: `python3 dashboard_server_simple.py`
2. **Open browser**: Navigate to `http://localhost:8082`
3. **Inject anomalies**: Use the preset buttons
4. **Monitor flow**: Watch the reasoning trace and agent activity
5. **Check results**: Verify email reports and phone calls

## 📊 Log Format

The system works with structured JSON logs:

```json
{
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
  "anomaly": false
}
```

## 🔍 Troubleshooting

### Common Issues

#### 1. **Dashboard Not Loading**
```bash
# Check if server is running
curl http://localhost:8082/api/health

# Restart server
pkill -f dashboard_server_simple
python3 dashboard_server_simple.py
```

#### 2. **Kafka Connection Issues**
```bash
# Check Kafka status
docker-compose ps

# Restart Kafka
docker-compose restart kafka

# Check logs
docker-compose logs kafka
```

#### 3. **API Key Issues**
```bash
# Verify configuration
python3 -c "import config; print('Config loaded successfully')"

# Check environment variables
echo $OPENAI_API_KEY
```

#### 4. **ML Model Issues**
```bash
# Check model files
ls -la ml_pipeline/saved_models/

# Test ML orchestrator
python3 tests/test_ml_orchestrator.py
```

### Debug Commands

```bash
# View all logs
tail -f logs/dashboard.log

# Check running processes
ps aux | grep python

# Monitor system resources
htop

# Check Docker containers
docker-compose ps
```

## 🚀 Production Deployment

### Docker Deployment

```bash
# Build production image
docker build -t aegis-sre-agent .

# Run with production config
docker run -d \
  -p 8082:8082 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID \
  aegis-sre-agent
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aegis-sre-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aegis-sre-agent
  template:
    metadata:
      labels:
        app: aegis-sre-agent
    spec:
      containers:
      - name: aegis-sre-agent
        image: aegis-sre-agent:latest
        ports:
        - containerPort: 8082
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: aegis-secrets
              key: openai-api-key
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **OpenAI** for GPT-4 integration
- **Twilio** for phone paging capabilities
- **SendGrid** for email delivery
- **Apache Kafka** for real-time streaming
- **Scikit-learn** for ML capabilities

## 📞 Support

For support and questions:
- **Email**: sre-support@yourcompany.com
- **Slack**: #sre-agent-support
- **Documentation**: [Wiki Link]

---

