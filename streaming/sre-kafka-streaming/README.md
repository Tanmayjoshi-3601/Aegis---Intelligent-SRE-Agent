# 🚀 Intelligent SRE Agent - Real-Time Anomaly Detection & Automated Mitigation

A comprehensive Site Reliability Engineering (SRE) system that combines Machine Learning anomaly detection, RAG-based knowledge retrieval, and automated mitigation strategies with real-time monitoring and human escalation capabilities.

![SRE Dashboard](https://img.shields.io/badge/Status-Production%20Ready-green)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![ML](https://img.shields.io/badge/ML-Scikit--learn-orange)
![Kafka](https://img.shields.io/badge/Kafka-Streaming-red)
![Twilio](https://img.shields.io/badge/Twilio-Paging-blue)
![SendGrid](https://img.shields.io/badge/SendGrid-Email-green)

## 🎯 Overview

This Intelligent SRE Agent system provides end-to-end automation for detecting, analyzing, and resolving system anomalies in real-time. It combines multiple AI agents working in orchestration to provide intelligent, automated incident response with human oversight for critical issues.

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
cd sre-kafka-streaming
```

### 2. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dashboard.txt

# Or use the automated installer
chmod +x install.sh
./install.sh
```

### 3. Configure API Keys

Create a `config.py` file with your API credentials:

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

### 4. Start Infrastructure

```bash
# Start Kafka, Zookeeper, Redis, and PostgreSQL
docker-compose up -d

# Wait for services to be ready (about 30 seconds)
sleep 30
```

### 5. Start the SRE Dashboard

```bash
# Start the dashboard server
python3 dashboard_server_simple.py

# Or use the automated startup script
chmod +x start_dashboard.sh
./start_dashboard.sh
```

### 6. Access the Dashboard

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
python3 test_complete_system.py
```

### Test Individual Components

```bash
# Test ML Orchestrator
python3 test_ml_orchestrator.py

# Test RAG Agent
python3 test_rag_agent.py

# Test Mitigation Agent
python3 test_streaming.py
```

### Manual Testing via Dashboard

1. **Start the dashboard**: `python3 dashboard_server_simple.py`
2. **Open browser**: Navigate to `http://localhost:8082`
3. **Inject anomalies**: Use the preset buttons
4. **Monitor flow**: Watch the reasoning trace and agent activity
5. **Check results**: Verify email reports and phone calls

## 📁 Project Structure

```
sre-kafka-streaming/
├── agents/                          # SRE Agent implementations
│   ├── anomaly_detector_agent.py    # ML-based anomaly detection
│   ├── rag_agent.py                 # RAG knowledge retrieval
│   ├── mitigation_agent.py          # Automated mitigation
│   ├── advanced_llm_agent.py        # Critical issue analysis
│   ├── report_generation_agent.py   # Email report generation
│   └── paging_agent.py              # Twilio phone paging
├── orchestration/                   # Orchestration components
│   ├── validation_simulator.py      # Mitigation validation
│   └── ml_orchestrator.py           # ML model orchestration
├── frontend/                        # Dashboard frontend
│   ├── index.html                   # Main dashboard
│   ├── styles.css                   # Dashboard styling
│   └── js/                          # JavaScript components
├── data/                            # Sample data and logs
├── scripts/                         # Database and setup scripts
├── config.py                        # Configuration file
├── dashboard_server_simple.py       # Main dashboard server
├── requirements.txt                 # Python dependencies
├── docker-compose.yml               # Infrastructure setup
└── README.md                        # This file
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
python3 test_ml_orchestrator.py
```

### Debug Commands

```bash
# View all logs
tail -f dashboard.log

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
docker build -t sre-agent .

# Run with production config
docker run -d \
  -p 8082:8082 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e TWILIO_ACCOUNT_SID=$TWILIO_ACCOUNT_SID \
  sre-agent
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sre-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: sre-agent
  template:
    metadata:
      labels:
        app: sre-agent
    spec:
      containers:
      - name: sre-agent
        image: sre-agent:latest
        ports:
        - containerPort: 8082
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: sre-secrets
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

**Made with ❤️ for SRE teams worldwide** 