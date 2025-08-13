# Kafka Streaming Setup Guide

## Overview

This guide explains how to set up and run the Kafka streaming infrastructure for the SRE (Site Reliability Engineering) application. The Kafka setup enables real-time log streaming and monitoring of your application services.

## Prerequisites

- **Docker Desktop**: Must be running
- **Python 3.12**: With the `sre` conda environment activated
- **Ports Available**: 2182 (Zookeeper), 9093 (Kafka), 8081 (Kafka UI)

## Quick Start

### 1. Start Kafka Infrastructure

```bash
# Navigate to the project directory
cd /Volumes/Personal/Northeastern/Prompt\ course/Aegis---Intelligent-SRE-Agent

# Start Kafka services using the provided script
./start_sre_streaming.sh start
```

This will start:
- **Zookeeper** (port 2182)
- **Kafka Broker** (port 9093)
- **Kafka UI** (port 8081)

### 2. Verify Kafka is Running

```bash
# Check if containers are running
docker ps

# You should see:
# - sre-zookeeper
# - sre-kafka  
# - sre-kafka-ui
```

### 3. Access Kafka UI

Open your browser and go to: **http://localhost:8081**

You should see the Kafka UI dashboard with:
- Topics overview
- Message monitoring
- Consumer groups
- Real-time streaming data

## Streaming Your Application Logs

### Option 1: Direct Log Streaming (Recommended)

```bash
# Activate the SRE environment
conda activate sre

# Stream your application logs to Kafka
python stream_logs_direct.py
```

This script will:
- Load logs from `data/synthetic/training/logs.json`
- Stream them to the `system-logs` topic
- Display real-time progress
- Show statistics when complete

### Option 2: Full Integration Service

```bash
# Run the complete streaming integration
python streaming_integration.py --mode normal --rate 3 --duration 30 --kafka-servers 127.0.0.1:9093
```

**Parameters:**
- `--mode`: `normal`, `burst`, or `scenario`
- `--rate`: Logs per second (default: 3)
- `--duration`: Duration in seconds (default: 30)
- `--kafka-servers`: Kafka broker address (default: 127.0.0.1:9093)

## Monitoring Your Streams

### 1. Kafka UI Dashboard

Navigate to **Topics → system-logs → Messages** to see:
- Real-time log messages
- Message details and metadata
- Timestamps and service information
- Log levels (INFO, WARNING, ERROR, CRITICAL)

### 2. Command Line Monitoring

```bash
# View messages in real-time
docker exec sre-kafka kafka-console-consumer \
  --bootstrap-server localhost:9093 \
  --topic system-logs \
  --from-beginning

# View latest messages only
docker exec sre-kafka kafka-console-consumer \
  --bootstrap-server localhost:9093 \
  --topic system-logs
```

## Service Management

### Start Services

```bash
./start_sre_streaming.sh start
```

### Stop Services

```bash
./start_sre_streaming.sh stop
```

### Check Status

```bash
./start_sre_streaming.sh status
```

### Clean Up

```bash
./start_sre_streaming.sh cleanup
```

## Troubleshooting

### Port Conflicts

If you see "port already in use" errors:

```bash
# Check what's using the ports
lsof -i :2182  # Zookeeper
lsof -i :9093  # Kafka
lsof -i :8081  # Kafka UI

# Kill conflicting processes if needed
kill -9 <PID>
```

### Connection Issues

If the Python streaming service can't connect:

1. **Verify Kafka is running:**
   ```bash
   docker ps | grep sre-kafka
   ```

2. **Test connectivity:**
   ```bash
   nc -vz localhost 9093
   ```

3. **Use the direct streaming method:**
   ```bash
   python stream_logs_direct.py
   ```

### Container Issues

```bash
# Restart all services
./start_sre_streaming.sh stop
./start_sre_streaming.sh start

# View logs
docker logs sre-kafka
docker logs sre-zookeeper
docker logs sre-kafka-ui
```

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SRE App       │    │   Kafka         │    │   Kafka UI      │
│   Logs          │───▶│   Broker        │───▶│   Dashboard     │
│                 │    │   (Port 9093)   │    │   (Port 8081)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Zookeeper     │
                       │   (Port 2182)   │
                       └─────────────────┘
```

## Data Flow

1. **Application Logs**: Loaded from `data/synthetic/training/logs.json`
2. **Streaming**: Sent to Kafka `system-logs` topic
3. **Processing**: Real-time analysis and monitoring
4. **Visualization**: Displayed in Kafka UI dashboard

## Log Format

Your application logs follow this JSON format:

```json
{
  "timestamp": 1234567890,
  "service": "database-primary",
  "level": "WARNING",
  "message": "Connection pool at 80% capacity",
  "metrics": {
    "cpu_usage": 75.5,
    "memory_usage": 68.2,
    "error_rate": 0.1,
    "request_latency_ms": 150.0,
    "active_connections": 850
  },
  "source": "sre-application",
  "stream_metadata": {
    "streamed_at": "2025-08-12T19:45:00.000Z",
    "stream_sequence": 42,
    "producer_id": "sre-app-direct-streamer"
  }
}
```

## Next Steps

1. **Monitor your streams** in the Kafka UI
2. **Analyze log patterns** for anomalies
3. **Set up alerts** for critical issues
4. **Scale the infrastructure** as needed
5. **Integrate with ML models** for anomaly detection

## Support

For issues or questions:
- Check the troubleshooting section above
- Review Docker container logs
- Verify network connectivity
- Ensure all prerequisites are met
