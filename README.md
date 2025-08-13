# Aegis - Intelligent SRE Agent

An intelligent Site Reliability Engineering (SRE) agent that uses machine learning for real-time log analysis, anomaly detection, and automated incident response.

## Features

- 🤖 **ML-Powered Anomaly Detection**: Real-time analysis using trained machine learning models
- 📊 **Comprehensive Log Analysis**: Support for multiple log formats and services
- 🔄 **Real-time Streaming**: Kafka-based streaming pipeline for live log processing
- 📈 **Synthetic Data Generation**: Generate realistic log data for testing and training
- 🎯 **Multi-Service Support**: Analyze logs from multiple microservices
- 📋 **Automated Playbooks**: Pre-defined response playbooks for common incidents

## Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Or use conda
conda activate sre
pip install -r requirements.txt
```

### 2. Generate Synthetic Data

```bash
# Generate training data
python synthetic_data_generator.py --training

# Generate streaming data
python synthetic_data_generator.py --streaming
```

### 3. Train ML Models

```bash
# Train anomaly detection models
python ml_pipeline/anomaly_detector.py --train
```

### 4. Start Real-time Streaming

```bash
# Start the complete streaming pipeline (requires Docker)
./start_sre_streaming.sh start

# Verify Kafka services are running
docker ps

# Access Kafka UI at http://localhost:8081
```

### 5. Stream Your Application Logs

```bash
# Stream logs to Kafka (recommended method)
python stream_logs_direct.py

# Or use the full integration service
python streaming_integration.py --mode normal --rate 3 --duration 30 --kafka-servers 127.0.0.1:9093
```

**Monitor your streams:**
- Open **http://localhost:8081** in your browser
- Navigate to **Topics → system-logs → Messages**
- See real-time log streaming from your application

## Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│   SRE App       │───▶│    Kafka     │───▶│  Log Consumer   │───▶│   ML Model   │
│   (Log Source)  │    │   (Docker)   │    │   (Python)      │    │  (Analysis)  │
└─────────────────┘    └──────────────┘    └─────────────────┘    └──────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │   Monitor    │
                       │   (Python)   │
                       └──────────────┘
```

## Components

### Core Application
- **`synthetic_data_generator.py`**: Generate realistic log data for training and testing
- **`ml_pipeline/anomaly_detector.py`**: ML pipeline for anomaly detection
- **`data/`**: Training and streaming log data

### Streaming Integration
- **`streaming_integration.py`**: Main streaming service with ML integration
- **`start_sre_streaming.sh`**: Complete pipeline startup script
- **`sre-kafka-streaming/`**: Kafka infrastructure and monitoring tools

### Testing & Validation
- **`stream_logs_direct.py`**: Direct log streaming to Kafka (recommended)
- **`streaming_integration.py`**: Full streaming service with ML integration
- **`KAFKA_SETUP_GUIDE.md`**: Comprehensive Kafka setup and usage guide

## Usage Examples

### Basic Streaming

```bash
# Start Kafka infrastructure
./start_sre_streaming.sh start

# Stream your application logs
python stream_logs_direct.py
```

### High-Volume Streaming

```bash
# Stream at higher rates using the integration service
python streaming_integration.py --mode normal --rate 10 --duration 60 --kafka-servers 127.0.0.1:9093
```

### Burst Mode (Simulate High Load)

```bash
# Stream in bursts to simulate traffic spikes
python streaming_integration.py --mode burst --rate 20 --duration 30 --kafka-servers 127.0.0.1:9093
```

### Limited Duration

```bash
# Run for 30 minutes then stop
python streaming_integration.py --mode normal --rate 3 --duration 1800 --kafka-servers 127.0.0.1:9093
```

## Log Format

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

## ML Pipeline

The ML pipeline automatically:
- Extracts features from logs (CPU, memory, error rates, etc.)
- Detects anomalies using trained models
- Provides confidence scores and anomaly types
- Integrates with real-time streaming

### Supported Anomaly Types
- High CPU usage
- High memory usage
- High error rates
- High latency
- Connection pool exhaustion
- Disk issues
- Network issues

## Monitoring

### Real-time Statistics
```
📊 Progress: 1000 logs sent, 45 anomalies, 2 errors, Rate: 10.2 logs/sec
```

### Kafka Monitoring
```bash
# Check status
./start_sre_streaming.sh status

# View Kafka topics
docker exec sre-kafka kafka-topics --bootstrap-server localhost:9093 --list

# Monitor messages in real-time
docker exec sre-kafka kafka-console-consumer --bootstrap-server localhost:9093 --topic system-logs --from-beginning
```

## Prerequisites

- Python 3.8+
- Docker Desktop (for Kafka streaming)
- Required Python packages (see requirements.txt)

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Aegis---Intelligent-SRE-Agent
   ```

2. **Set up Python environment**
   ```bash
   conda create -n sre python=3.12
   conda activate sre
   pip install -r requirements.txt
   ```

3. **Generate data and train models**
   ```bash
   python synthetic_data_generator.py --training --streaming
   python ml_pipeline/anomaly_detector.py --train
   ```

4. **Test the streaming**
   ```bash
   python stream_logs_direct.py
   ```

## Configuration

### Streaming Configuration
Edit `StreamingConfig` in `streaming_integration.py`:
- Kafka connection settings
- Streaming rates and modes
- ML pipeline options
- Monitoring settings

### Kafka Configuration
Edit `sre-kafka-streaming/docker-compose.yml`:
- Memory limits
- Port configurations
- Volume mounts

## Troubleshooting

### Common Issues

1. **Docker not running**
   ```bash
   # Start Docker Desktop first
   ./start_sre_streaming.sh start
   ```

2. **Kafka connection failed**
   ```bash
   ./start_sre_streaming.sh status
   ./start_sre_streaming.sh restart
   ```

3. **ML model not found**
   ```bash
   python ml_pipeline/anomaly_detector.py --train
   ```

4. **Kafka connection issues**
   ```bash
   # Use the direct streaming method
   python stream_logs_direct.py
   
   # Or check Kafka status
   ./start_sre_streaming.sh status
   ```

### Debug Commands

```bash
# Test streaming
python stream_logs_direct.py

# Check status
./start_sre_streaming.sh status

# View logs
docker logs sre-kafka

# Monitor Kafka messages
docker exec sre-kafka kafka-console-consumer --bootstrap-server localhost:9093 --topic system-logs
```

## Development

### Project Structure
```
Aegis---Intelligent-SRE-Agent/
├── ml_pipeline/              # ML models and training
├── data/                     # Training and streaming data
├── sre-kafka-streaming/      # Kafka infrastructure
├── streaming_integration.py  # Main streaming service
├── stream_logs_direct.py     # Direct log streaming (recommended)
├── start_sre_streaming.sh    # Startup script
└── requirements.txt          # Python dependencies
```

### Adding New Features
1. Extend the log format in `synthetic_data_generator.py`
2. Add new features to the ML pipeline in `ml_pipeline/anomaly_detector.py`
3. Update streaming integration in `streaming_integration.py`
4. Test streaming with `stream_logs_direct.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For questions and support:
- Check the troubleshooting section
- Review the Kafka setup guide: `KAFKA_SETUP_GUIDE.md`
- Test streaming: `python stream_logs_direct.py`