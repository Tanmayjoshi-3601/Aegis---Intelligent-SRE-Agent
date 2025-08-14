# Intelligent SRE Agent System

## Overview

The Intelligent SRE Agent System is a sophisticated, multi-agent orchestration platform that processes streaming logs through Kafka and automatically detects, analyzes, and mitigates system anomalies. The system uses machine learning for anomaly detection and intelligent agents for decision-making and automated response.

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│   Kafka Logs    │───▶│  SRE Agent   │───▶│  Agent Pipeline │───▶│   Actions    │
│   (Streaming)   │    │ Orchestrator │    │                 │    │              │
└─────────────────┘    └──────────────┘    └─────────────────┘    └──────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │   Database   │
                       │   Storage    │
                       └──────────────┘
```

### Agent Pipeline Flow

1. **Anomaly Detection Agent** - ML-based anomaly detection
2. **Mitigation Agent** - Determines if error is common or uncommon
3. **RAG Agent** - Handles common errors with playbooks
4. **Advanced LLM Agent** - Handles uncommon errors with custom analysis
5. **Database Agent** - Stores normal logs
6. **Paging Agent** - Human notifications for critical incidents

## Features

### 🤖 Multi-Agent Orchestration
- **Anomaly Detection**: ML-powered anomaly detection with confidence scoring
- **Intelligent Classification**: Automatic classification of errors as common vs uncommon
- **Automated Response**: Pre-defined playbooks for common errors
- **Advanced Analysis**: LLM-powered analysis for complex incidents
- **Human Escalation**: Smart paging system for critical incidents

### 📊 Real-time Processing
- **Kafka Integration**: Seamless integration with existing Kafka streaming
- **High Throughput**: Async processing for high-volume log streams
- **Low Latency**: Sub-second processing times
- **Fault Tolerance**: Error handling and retry mechanisms

### 🎯 Intelligent Decision Making
- **Confidence Scoring**: All decisions include confidence levels
- **Historical Learning**: Pattern recognition from past incidents
- **Context Awareness**: Comprehensive analysis of system metrics
- **Risk Assessment**: Automatic risk evaluation for actions

### 🔧 Automated Actions
- **Service Restarts**: Automated service recovery
- **Scaling Operations**: Automatic resource scaling
- **Configuration Updates**: Dynamic configuration changes
- **Monitoring Setup**: Automated monitoring and alerting

## Quick Start

### Prerequisites

- Python 3.8+
- Docker (for Kafka)
- Kafka cluster running
- ML models (optional, fallback detection available)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd sre-kafka-streaming
```

2. **Install dependencies**
```bash
pip install -r requirements-streaming.txt
pip install kafka-python asyncio sqlite3
```

3. **Start Kafka infrastructure**
```bash
./run_pipeline.sh
```

4. **Start the SRE Agent system**
```bash
python kafka_sre_integration.py
```

### Configuration

The system is configured via `config/sre_agent_config.json`:

```json
{
  "agents": {
    "anomaly_detector": {
      "enabled": true,
      "confidence_threshold": 0.7
    },
    "mitigation": {
      "enabled": true,
      "common_error_threshold": 0.8
    }
  },
  "kafka": {
    "bootstrap_servers": "localhost:9092",
    "topic": "system-logs",
    "consumer_group": "sre-agent-group"
  }
}
```

## Usage Examples

### Basic Log Processing

```python
from sre_agent_orchestrator import SREAgentOrchestrator

# Initialize orchestrator
orchestrator = SREAgentOrchestrator()

# Process a log entry
log_data = {
    "timestamp": "2025-08-12T17:09:17.944835",
    "service": "database-primary",
    "level": "ERROR",
    "metrics": {
        "cpu_usage": 95.5,
        "memory_usage": 87.2,
        "error_rate": 0.15
    },
    "message": "Database connection pool exhausted"
}

result = await orchestrator.process_log(log_data)
print(f"Decision: {result['decisions']}")
print(f"Actions: {result['actions_taken']}")
```

### Custom Agent Configuration

```python
from agents.anomaly_detector_agent import AnomalyDetectorAgent
from agents.rag_agent import RAGAgent

# Custom anomaly detector
anomaly_agent = AnomalyDetectorAgent(
    model_path="custom_models/",
    confidence_threshold=0.8
)

# Custom RAG agent
rag_agent = RAGAgent(
    knowledge_base_path="custom_playbooks/",
    max_context_length=8000
)
```

## Agent Details

### Anomaly Detection Agent

**Purpose**: Detect anomalies in system logs using ML models

**Features**:
- ML model integration (with fallback rule-based detection)
- Confidence scoring
- Multiple metric analysis
- Historical pattern recognition

**Configuration**:
```json
{
  "model_path": "ml_pipeline/saved_models",
  "confidence_threshold": 0.7
}
```

### Mitigation Agent

**Purpose**: Classify errors as common or uncommon

**Features**:
- Pattern matching against known error types
- Historical frequency analysis
- Service-specific error patterns
- Confidence-based classification

**Configuration**:
```json
{
  "common_error_threshold": 0.8,
  "db_path": "data/sre_agent.db"
}
```

### RAG Agent

**Purpose**: Handle common errors with retrieval-augmented generation

**Features**:
- Pre-defined playbooks for common scenarios
- Automated action execution
- Risk assessment
- Rollback capabilities

**Configuration**:
```json
{
  "knowledge_base_path": "data/knowledge_base",
  "max_context_length": 4000
}
```

### Advanced LLM Agent

**Purpose**: Handle uncommon errors with sophisticated analysis

**Features**:
- LLM-powered root cause analysis
- Custom solution generation
- Impact assessment
- Escalation planning

**Configuration**:
```json
{
  "model": "gpt-4",
  "max_tokens": 2000
}
```

### Database Agent

**Purpose**: Store and retrieve log data

**Features**:
- SQLite database for log storage
- Statistical analysis
- Historical data retrieval
- Automatic cleanup

**Configuration**:
```json
{
  "db_path": "data/sre_agent.db"
}
```

### Paging Agent

**Purpose**: Human notifications and escalation

**Features**:
- Multi-channel notifications (email, webhook)
- Escalation policies
- Incident tracking
- Acknowledgment and resolution

**Configuration**:
```json
{
  "paging_webhook": "https://api.pagerduty.com/v2/incidents",
  "escalation_policy": "default"
}
```

## Monitoring and Metrics

### System Statistics

The system provides comprehensive statistics:

```python
# Get orchestrator stats
stats = orchestrator.get_stats()
print(f"Total logs processed: {stats['total_logs_processed']}")
print(f"Anomalies detected: {stats['anomalies_detected']}")
print(f"Pages sent: {stats['pages_sent']}")

# Get individual agent stats
anomaly_stats = anomaly_agent.get_stats()
rag_stats = rag_agent.get_stats()
```

### Log Files

- `logs/sre_agent.log` - Main system logs
- `data/sre_agent.db` - SQLite database with logs and statistics

### Health Checks

```python
# Check system health
health = await orchestrator.health_check()
print(f"System healthy: {health['healthy']}")
print(f"Active agents: {health['active_agents']}")
```

## Error Handling

### Graceful Degradation

The system is designed to handle failures gracefully:

- **ML Model Unavailable**: Falls back to rule-based detection
- **Database Errors**: Continues processing with in-memory storage
- **Network Issues**: Retries with exponential backoff
- **Agent Failures**: Continues with remaining agents

### Error Recovery

```python
# Handle processing errors
try:
    result = await orchestrator.process_log(log_data)
except Exception as e:
    logger.error(f"Processing failed: {e}")
    # Implement recovery logic
```

## Performance Tuning

### Throughput Optimization

```json
{
  "processing": {
    "batch_size": 100,
    "max_retries": 3,
    "timeout_seconds": 30
  }
}
```

### Memory Management

- Automatic log cleanup (configurable retention)
- Database optimization
- Async processing to prevent blocking

## Security Considerations

### Data Protection

- Log data encryption at rest
- Secure communication channels
- Access control for sensitive operations
- Audit logging for all actions

### Agent Security

- Sandboxed execution environments
- Command validation and sanitization
- Risk assessment before action execution
- Rollback mechanisms for failed actions

## Troubleshooting

### Common Issues

1. **Kafka Connection Failed**
   ```bash
   # Check Kafka status
   docker ps | grep kafka
   
   # Verify topic exists
   kafka-topics --list --bootstrap-server localhost:9092
   ```

2. **ML Model Loading Failed**
   ```bash
   # Check model files
   ls -la ml_pipeline/saved_models/
   
   # Verify dependencies
   pip list | grep joblib
   ```

3. **Database Errors**
   ```bash
   # Check database file
   ls -la data/sre_agent.db
   
   # Verify permissions
   chmod 644 data/sre_agent.db
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## Contributing

### Adding New Agents

1. Create agent class in `agents/` directory
2. Implement required interface methods
3. Add configuration options
4. Update orchestrator integration
5. Add tests

### Extending Playbooks

1. Add playbook to `data/knowledge_base/mitigation_playbooks.json`
2. Define actions and risk levels
3. Test with sample scenarios
4. Update documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Create an issue in the repository
- Check the troubleshooting section
- Review the configuration examples
- Consult the agent documentation

---

**Note**: This is a production-ready implementation with comprehensive error handling, monitoring, and scalability features. The system is designed to handle real-world SRE scenarios with intelligent automation and human oversight. 