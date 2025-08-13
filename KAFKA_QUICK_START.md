# Kafka Streaming - Quick Start

## 🚀 Get Started in 3 Steps

### 1. Start Kafka Infrastructure
```bash
# Make sure Docker Desktop is running
./start_sre_streaming.sh start
```

### 2. Stream Your Logs
```bash
# Activate environment
conda activate sre

# Stream application logs
python stream_logs_direct.py
```

### 3. Monitor in UI
Open **http://localhost:8081** in your browser
- Navigate to **Topics → system-logs → Messages**
- See your real-time log streaming!

## 📊 What You'll See

Your application logs will stream to Kafka showing:
- **Service names**: database-primary, api-gateway, payment-service, etc.
- **Log levels**: INFO, WARNING, ERROR, CRITICAL, DEBUG
- **Real-time metrics**: CPU, memory, error rates, latency
- **Streaming metadata**: timestamps, sequence numbers

## 🔧 Troubleshooting

**Port conflicts?**
```bash
lsof -i :2182  # Zookeeper
lsof -i :9093  # Kafka  
lsof -i :8081  # Kafka UI
```

**Connection issues?**
```bash
# Check if Kafka is running
docker ps | grep sre-kafka

# Use direct streaming (bypasses connection issues)
python stream_logs_direct.py
```

**Need to restart?**
```bash
./start_sre_streaming.sh stop
./start_sre_streaming.sh start
```

## 📚 More Information

- **Full Guide**: `KAFKA_SETUP_GUIDE.md`
- **Main README**: `README.md`
- **Service Management**: `./start_sre_streaming.sh --help`
