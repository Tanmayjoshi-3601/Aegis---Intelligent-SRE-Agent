# quick_start_streaming.py
"""
Quick start script to stream your generated logs through Kafka
"""
import json
import time
import sys
from pathlib import Path
import subprocess
import logging
from typing import Dict, Any, List

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_kafka_running():
    """Check if Kafka is running"""
    try:
        # Try to connect to Kafka
        from kafka import KafkaProducer
        producer = KafkaProducer(bootstrap_servers='localhost:9092')
        producer.close()
        return True
    except:
        return False

def start_kafka_services():
    """Start Kafka using docker-compose"""
    logger.info("Starting Kafka services...")
    try:
        subprocess.run(["docker-compose", "up", "-d", "zookeeper", "kafka"], check=True)
        logger.info("Waiting for Kafka to be ready...")
        time.sleep(10)
        return True
    except subprocess.CalledProcessError:
        logger.error("Failed to start Kafka. Make sure Docker is running.")
        return False

def create_kafka_topic():
    """Create the system-logs topic"""
    try:
        subprocess.run([
            "docker", "exec", "sre-kafka",
            "kafka-topics", "--bootstrap-server", "localhost:9092",
            "--create", "--topic", "system-logs",
            "--partitions", "3", "--replication-factor", "1",
            "--if-not-exists"
        ], check=True, capture_output=True)
        logger.info("Kafka topic 'system-logs' ready")
        return True
    except:
        logger.warning("Could not create topic (may already exist)")
        return True

def parse_your_logs(log_data: str) -> List[Dict[str, Any]]:
    """Parse your log format"""
    logs = []
    
    # Try to parse as JSON array
    try:
        # Remove any trailing commas and fix JSON formatting
        log_data = log_data.strip()
        if log_data.endswith(','):
            log_data = log_data[:-1]
        
        # If it's not wrapped in array brackets, wrap it
        if not log_data.startswith('['):
            log_data = '[' + log_data + ']'
            
        logs = json.loads(log_data)
        logger.info(f"Parsed {len(logs)} logs as JSON array")
        return logs
    except:
        pass
    
    # Try to parse as individual JSON objects
    try:
        # Split by },{ pattern
        log_entries = log_data.replace('},\n{', '}|||{').split('|||')
        
        for entry in log_entries:
            entry = entry.strip()
            if not entry:
                continue
                
            # Ensure proper JSON formatting
            if not entry.startswith('{'):
                entry = '{' + entry
            if not entry.endswith('}'):
                entry = entry + '}'
                
            try:
                log = json.loads(entry)
                logs.append(log)
            except:
                continue
                
        logger.info(f"Parsed {len(logs)} logs as individual JSON objects")
        return logs
    except Exception as e:
        logger.error(f"Failed to parse logs: {e}")
        return []

def stream_your_logs(log_file: str, metadata_file: str, mode: str = "normal"):
    """Stream your specific logs through Kafka"""
    
    from kafka import KafkaProducer
    import random
    
    # Load metadata
    with open(metadata_file, 'r') as f:
        metadata = json.load(f)
    
    logger.info(f"Loaded metadata: {metadata['total_logs']} logs with {len(metadata['scenarios'])} scenarios")
    
    # Load and parse logs
    with open(log_file, 'r') as f:
        log_data = f.read()
    
    logs = parse_your_logs(log_data)
    
    if not logs:
        logger.error("No logs parsed!")
        return
    
    logger.info(f"Successfully parsed {len(logs)} logs")
    
    # Connect to Kafka
    producer = KafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        compression_type='gzip'
    )
    
    logger.info(f"Starting to stream in {mode} mode...")
    
    # Count anomalies
    anomaly_count = sum(1 for log in logs if log.get('anomaly', False))
    logger.info(f"Dataset contains {anomaly_count} anomalies ({anomaly_count/len(logs)*100:.1f}%)")
    
    # Stream based on mode
    if mode == "realtime":
        # Stream following actual timestamps
        stream_realtime(producer, logs, metadata)
    elif mode == "scenario":
        # Stream specific scenarios
        stream_scenarios(producer, logs, metadata)
    elif mode == "burst":
        # Stream with burst patterns
        stream_burst(producer, logs)
    else:
        # Normal streaming
        stream_normal(producer, logs)
    
    producer.flush()
    producer.close()
    logger.info("Streaming complete!")

def stream_normal(producer, logs, rate=10):
    """Stream at constant rate"""
    interval = 1.0 / rate
    sent = 0
    anomalies = 0
    
    for log in logs:
        # Add streaming metadata
        log['stream_time'] = time.time()
        log['stream_mode'] = 'normal'
        
        # Send to Kafka
        producer.send(
            'system-logs',
            key=log.get('service', 'unknown').encode('utf-8'),
            value=log
        )
        
        sent += 1
        if log.get('anomaly', False):
            anomalies += 1
        
        # Progress update
        if sent % 100 == 0:
            logger.info(f"Progress: {sent}/{len(logs)} logs sent ({anomalies} anomalies)")
        
        time.sleep(interval)
    
    logger.info(f"Sent {sent} logs with {anomalies} anomalies")

def stream_realtime(producer, logs, metadata):
    """Stream following timestamp patterns"""
    # Sort logs by timestamp
    sorted_logs = sorted(logs, key=lambda x: x.get('timestamp', ''))
    
    logger.info("Streaming in timestamp order...")
    
    # Calculate time differences
    if len(sorted_logs) > 1:
        first_time = sorted_logs[0].get('timestamp', '')
        last_time = sorted_logs[-1].get('timestamp', '')
        logger.info(f"Time range: {first_time} to {last_time}")
    
    sent = 0
    for i, log in enumerate(sorted_logs):
        log['stream_time'] = time.time()
        log['stream_mode'] = 'realtime'
        
        producer.send(
            'system-logs',
            key=log.get('service', 'unknown').encode('utf-8'),
            value=log
        )
        
        sent += 1
        
        # Simulate time gaps
        if i < len(sorted_logs) - 1:
            # Check if next log is from a different minute
            current_time = log.get('timestamp', '')
            next_time = sorted_logs[i + 1].get('timestamp', '')
            
            if current_time[:16] != next_time[:16]:  # Different minute
                time.sleep(0.5)  # Larger gap
            else:
                time.sleep(0.05)  # Small gap
        
        if sent % 100 == 0:
            logger.info(f"Progress: {sent}/{len(sorted_logs)} logs sent")
    
    logger.info(f"Realtime streaming complete: {sent} logs")

def stream_scenarios(producer, logs, metadata):
    """Stream specific scenarios"""
    for scenario in metadata['scenarios']:
        scenario_type = scenario['type']
        log_count = scenario['log_count']
        
        logger.info(f"Streaming scenario: {scenario_type} ({log_count} logs)")
        
        # Get subset of logs for this scenario
        scenario_logs = logs[:log_count]
        
        if scenario_type == 'ddos_attack':
            # Very fast streaming for DDoS
            for log in scenario_logs:
                log['stream_mode'] = 'ddos'
                log['scenario'] = scenario_type
                producer.send('system-logs', 
                            key=log.get('service', 'unknown').encode('utf-8'),
                            value=log)
                time.sleep(0.01)  # 100 logs/second
                
        elif scenario_type == 'memory_leak':
            # Gradual increase
            for i, log in enumerate(scenario_logs):
                log['stream_mode'] = 'memory_leak'
                log['scenario'] = scenario_type
                
                # Increase memory in metrics
                if 'metrics' in log:
                    base_memory = log['metrics'].get('memory_usage', 50)
                    log['metrics']['memory_usage'] = min(base_memory + (i * 2), 99)
                
                producer.send('system-logs',
                            key=log.get('service', 'unknown').encode('utf-8'),
                            value=log)
                time.sleep(0.1)
                
        elif scenario_type == 'cascading_failure':
            # Cascade pattern
            affected_services = set()
            for i, log in enumerate(scenario_logs):
                log['stream_mode'] = 'cascade'
                log['scenario'] = scenario_type
                
                # Spread failure
                if i < len(scenario_logs) * 0.3:
                    if not affected_services:
                        affected_services.add(log.get('service', 'unknown'))
                elif i < len(scenario_logs) * 0.7:
                    if len(affected_services) < 3:
                        affected_services.add(log.get('service', 'unknown'))
                
                if log.get('service') in affected_services:
                    log['anomaly'] = True
                
                producer.send('system-logs',
                            key=log.get('service', 'unknown').encode('utf-8'),
                            value=log)
                time.sleep(0.05)
        
        logger.info(f"Scenario {scenario_type} complete")
        time.sleep(2)  # Pause between scenarios

def stream_burst(producer, logs):
    """Stream with burst patterns"""
    logger.info("Burst mode streaming...")
    
    normal_rate = 5  # logs/second
    burst_rate = 50  # logs/second
    
    sent = 0
    for i, log in enumerate(logs):
        # Determine if we're in a burst
        if i % 200 < 50:  # Burst for 50 logs every 200 logs
            rate = burst_rate
            log['stream_mode'] = 'burst'
        else:
            rate = normal_rate
            log['stream_mode'] = 'normal'
        
        log['stream_time'] = time.time()
        
        producer.send('system-logs',
                     key=log.get('service', 'unknown').encode('utf-8'),
                     value=log)
        
        sent += 1
        time.sleep(1.0 / rate)
        
        if sent % 100 == 0:
            logger.info(f"Progress: {sent}/{len(logs)} logs sent")
    
    logger.info(f"Burst streaming complete: {sent} logs")

def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Quick start Kafka streaming for your logs")
    parser.add_argument("--logs", default="paste.txt", help="Path to your logs file")
    parser.add_argument("--metadata", default="metadata.json", help="Path to metadata file")
    parser.add_argument("--mode", choices=["normal", "realtime", "scenario", "burst"],
                       default="normal", help="Streaming mode")
    parser.add_argument("--setup", action="store_true", help="Setup Kafka first")
    
    args = parser.parse_args()
    
    # Setup if requested
    if args.setup:
        if not check_kafka_running():
            if not start_kafka_services():
                logger.error("Failed to start Kafka")
                sys.exit(1)
        
        if not create_kafka_topic():
            logger.error("Failed to create topic")
            sys.exit(1)
    
    # Check if Kafka is running
    if not check_kafka_running():
        logger.error("Kafka is not running. Use --setup flag or start it manually")
        sys.exit(1)
    
    # Stream logs
    try:
        stream_your_logs(args.logs, args.metadata, args.mode)
    except KeyboardInterrupt:
        logger.info("Streaming interrupted by user")
    except Exception as e:
        logger.error(f"Streaming failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
