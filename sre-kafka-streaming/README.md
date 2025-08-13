# SRE Kafka Streaming Pipeline

A comprehensive Kafka-based log streaming pipeline for SRE (Site Reliability Engineering) agent systems. This project provides real-time log processing, anomaly detection, and monitoring capabilities for microservices environments.

## 🚀 Features

- **Real-time Log Streaming**: Stream 2,728 synthetic logs through Kafka at configurable rates
- **Anomaly Detection**: Automatic detection of high CPU, memory, error rates, and latency issues
- **Multi-Service Support**: Monitor 10 different microservices with realistic scenarios
- **Scenario Simulation**: 18 different scenarios including cascading failures, memory leaks, and DDoS attacks
- **Real-time Monitoring**: Live dashboard with statistics and alerts
- **Cross-Platform**: Works on macOS, Linux, and Windows with Docker Desktop

## 📊 Data Overview

- **Total Logs**: 2,728
- **Anomalies**: 1,483 (54.4%)
- **Scenarios**: 18 (cascading failures, memory leaks, DDoS attacks)
- **Services**: 10 different microservices
- **Expected Anomaly Rate**: ~54%

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐
│   Log Producer  │───▶│    Kafka     │───▶│  Log Consumer   │
│   (Python)      │    │   (Docker)   │    │   (Python)      │
└─────────────────┘    └──────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │   Monitor    │
                       │   (Python)   │
                       └──────────────┘
```

## 📋 Prerequisites

- **Docker Desktop** (v20.10+)
- **Python 3.8+**
- **docker-compose** (usually included with Docker Desktop)
- **Git** (for cloning the repository)

## 🛠️ Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd sre-kafka-streaming
   ```

2. **Install Python dependencies**:
   ```bash
   pip install kafka-python
   ```

3. **Make scripts executable**:
   ```bash
   chmod +x run_pipeline.sh start_streaming.sh debug_commands.sh cleanup.sh
   ```

## 🚀 Quick Start

### Step 1: Setup the Pipeline

Run the setup script to start all services and create the Kafka topic:

```bash
./run_pipeline.sh
```

This script will:
- ✅ Check if Docker is running
- ✅ Start all Docker services (Kafka, Zookeeper, Redis, PostgreSQL, RabbitMQ, Kafka UI)
- ✅ Wait for services to be healthy
- ✅ Create the Kafka topic `system-logs`
- ✅ Verify everything is working

### Step 2: Test the Pipeline

Run the test script to verify the pipeline works end-to-end:

```bash
python3 test_streaming.py
```

This will:
- ✅ Send test logs to Kafka
- ✅ Consume them back
- ✅ Verify the pipeline works correctly
- ✅ Show success/failure status

### Step 3: Start Streaming

Run the streaming script to start the full pipeline:

```bash
./start_streaming.sh
```

This will:
- ✅ Open multiple terminal windows/tabs
- ✅ Start the producer in one terminal
- ✅ Start the consumer in another terminal
- ✅ Start the monitor in a third terminal

### Step 4: Monitor the Pipeline

The monitor will show:
- 📊 Real-time statistics
- 📈 Logs processed per second
- 🚨 Anomaly detection rate
- 🔧 Top anomalous services
- ⚠️ High-severity alerts

## 📖 Detailed Usage

### Manual Commands

If you prefer to run components manually:

#### Start Services
```bash
docker-compose up -d
```

#### Run Producer
```bash
python3 streaming/kafka/custom_log_streamer.py \
    --mode produce \
    --logs data/logs.json \
    --metadata data/metadata.json \
    --rate 10 \
    --scenario realistic
```

#### Run Consumer
```bash
python3 streaming/kafka/custom_log_streamer.py \
    --mode consume
```

#### Run Monitor
```bash
python3 monitor.py
```

### Streaming Scenarios

The pipeline supports different streaming scenarios:

- **`normal`**: Constant rate streaming
- **`realistic`**: Based on metadata scenarios (default)
- **`ddos_attack`**: High-rate burst patterns
- **`memory_leak`**: Gradual resource increase
- **`cascading_failure`**: Service failure propagation

### Configuration Options

#### Producer Options
- `--rate`: Logs per second (default: 10)
- `--scenario`: Streaming scenario (default: realistic)
- `--logs`: Path to logs file (default: data/logs.json)
- `--metadata`: Path to metadata file (default: data/metadata.json)

#### Consumer Options
- `--group-id`: Consumer group ID (default: sre-agent-consumer)
- `--auto-offset-reset`: Offset reset policy (default: latest)

## 🔍 Debugging and Troubleshooting

### Debug Commands

Use the debug script for troubleshooting:

```bash
./debug_commands.sh
```

Or run specific checks:

```bash
./debug_commands.sh connectivity  # Check Kafka connectivity
./debug_commands.sh topics        # List Kafka topics
./debug_commands.sh consumers     # Check consumer groups
./debug_commands.sh all           # Run all checks
```

### Common Issues

#### 1. Kafka Not Accessible
```bash
# Check if containers are running
docker ps

# Restart services
docker-compose restart

# Check Kafka logs
docker logs sre-kafka
```

#### 2. Topic Not Found
```bash
# Create topic manually
docker exec sre-kafka kafka-topics \
    --create \
    --topic system-logs \
    --bootstrap-server localhost:9092 \
    --partitions 3 \
    --replication-factor 1
```

#### 3. Consumer Group Issues
```bash
# Reset consumer group offsets
docker exec sre-kafka kafka-consumer-groups \
    --bootstrap-server localhost:9092 \
    --group sre-agent-consumer \
    --reset-offsets \
    --to-earliest \
    --execute \
    --all-topics
```

#### 4. Python Connection Issues
```bash
# Install kafka-python
pip install kafka-python

# Check Python version
python3 --version
```

### Monitoring URLs

- **Kafka UI**: http://localhost:8080
- **RabbitMQ Management**: http://localhost:15672
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🧹 Cleanup

### Stop Services Only
```bash
./cleanup.sh stop
```

### Soft Cleanup (Keep Data)
```bash
./cleanup.sh soft
```

### Full Cleanup (Remove Everything)
```bash
./cleanup.sh full
```

### Interactive Cleanup Menu
```bash
./cleanup.sh
```

## 📊 Expected Output

When everything runs correctly, you should see:

### Producer Output
```
📤 SRE Log Producer Started
==================================
Streaming logs to Kafka topic: system-logs
Progress: 100/2728 logs sent (54 anomalies)
Progress: 200/2728 logs sent (108 anomalies)
...
```

### Consumer Output
```
📥 SRE Log Consumer Started
==================================
Consuming logs from Kafka topic: system-logs
🚨 HIGH SEVERITY ALERT: database-primary - high_cpu, high_memory
📊 CONSUMPTION STATISTICS
Total Consumed: 1000
Anomalies Detected: 543
Detection Rate: 54.30%
```

### Monitor Output
```
📊 SRE KAFKA STREAMING PIPELINE MONITOR
============================================================
Uptime: 0:05:23 | Last Update: 14:30:15

📊 OVERALL STATISTICS
------------------------------
Total Logs Processed: 1,234
Anomalies Detected: 671
High Severity Events: 45
Overall Anomaly Rate: 54.38%

⚡ REAL-TIME METRICS (Last 60s)
-----------------------------------
Logs/Second: 10.2
Anomalies/Second: 5.5
Anomaly Rate: 54.1%

🔧 TOP ANOMALOUS SERVICES
-----------------------------------
1. database-primary
   Anomaly Rate: 78.5% 🚨
   Total Logs: 156
   Avg CPU: 89.2% | Avg Memory: 87.1%
   Avg Error Rate: 12.34% | Avg Latency: 678ms
```

## 🔧 Anomaly Detection Rules

The system detects anomalies when:

- **CPU Usage** > 85%
- **Memory Usage** > 85%
- **Error Rate** > 5%
- **Request Latency** > 500ms
- **Active Connections** > 450 (connection pool exhaustion)

## 📁 Project Structure

```
sre-kafka-streaming/
├── docker-compose.yml          # Docker services configuration
├── run_pipeline.sh            # Setup and start all services
├── test_streaming.py          # End-to-end pipeline test
├── start_streaming.sh         # Start producer/consumer/monitor
├── monitor.py                 # Real-time monitoring dashboard
├── debug_commands.sh          # Troubleshooting commands
├── cleanup.sh                 # Cleanup and reset scripts
├── README.md                  # This file
├── data/
│   ├── logs.json              # 2,728 synthetic logs
│   └── metadata.json          # Scenario metadata
└── streaming/
    └── kafka/
        └── custom_log_streamer.py  # Main streaming logic
```

## 🎯 Use Cases

### SRE Monitoring
- Real-time service health monitoring
- Anomaly detection and alerting
- Performance metrics tracking
- Incident response simulation

### Development and Testing
- Load testing with realistic scenarios
- Kafka pipeline development
- Monitoring system development
- Anomaly detection algorithm testing

### Learning and Training
- Kafka streaming concepts
- Real-time data processing
- SRE practices and tools
- Monitoring and alerting systems

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Run `./debug_commands.sh all` for comprehensive diagnostics
3. Check the logs: `docker-compose logs -f [service-name]`
4. Open an issue with detailed error information

## 🎉 Success Indicators

You'll know everything is working when you see:

- ✅ All Docker containers running
- ✅ Kafka topic `system-logs` created
- ✅ Producer streaming logs at ~10/second
- ✅ Consumer processing logs in real-time
- ✅ Monitor showing ~54% anomaly rate
- ✅ High-severity alerts for problematic services
- ✅ Kafka UI accessible at http://localhost:8080

Happy streaming! 🚀 