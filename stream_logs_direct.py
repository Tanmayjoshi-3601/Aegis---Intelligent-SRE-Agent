#!/usr/bin/env python3
"""
Direct Log Streaming to Kafka
=============================
This script loads your application logs and streams them directly to Kafka
using Docker exec commands, bypassing Python Kafka client connection issues.
"""

import json
import time
import subprocess
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

def load_application_logs() -> List[Dict[str, Any]]:
    """Load logs from your application's data directory"""
    logs = []
    
    # Try to load from different possible locations
    log_paths = [
        "data/synthetic/training/logs.json",
        "data/synthetic/validation/logs.json", 
        "data/synthetic/test/logs.json",
        "data/real/logs.json"
    ]
    
    for log_path in log_paths:
        if Path(log_path).exists():
            try:
                with open(log_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        logs.extend(data)
                    elif isinstance(data, dict) and 'logs' in data:
                        logs.extend(data['logs'])
                    else:
                        logs.append(data)
                print(f"✅ Loaded {len(logs)} logs from {log_path}")
                break
            except Exception as e:
                print(f"⚠️  Could not load from {log_path}: {e}")
    
    # If no logs found, create synthetic logs based on your application format
    if not logs:
        print("📝 Creating synthetic logs based on your application format...")
        services = ["database-primary", "user-service", "api-gateway", "payment-service", 
                   "inventory-service", "notification-service", "auth-service", "search-service"]
        
        levels = ["INFO", "WARNING", "ERROR", "CRITICAL"]
        
        for i in range(50):
            log = {
                "timestamp": int(time.time()) - random.randint(0, 86400),  # Last 24 hours
                "service": random.choice(services),
                "level": random.choice(levels),
                "message": f"Application log entry {i+1}",
                "metrics": {
                    "cpu_usage": random.uniform(10, 90),
                    "memory_usage": random.uniform(20, 85),
                    "error_rate": random.uniform(0, 5),
                    "request_latency_ms": random.uniform(10, 500),
                    "active_connections": random.randint(10, 1000)
                },
                "source": "sre-application",
                "streamed_at": datetime.utcnow().isoformat()
            }
            logs.append(log)
    
    return logs

def stream_log_to_kafka(log: Dict[str, Any], topic: str = "system-logs") -> bool:
    """Stream a single log to Kafka using Docker exec"""
    try:
        # Convert log to JSON string
        log_json = json.dumps(log)
        
        # Use Docker exec to send to Kafka
        cmd = [
            "docker", "exec", "-i", "sre-kafka",
            "kafka-console-producer",
            "--bootstrap-server", "localhost:9093",
            "--topic", topic
        ]
        
        result = subprocess.run(
            cmd,
            input=log_json,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return True
        else:
            print(f"❌ Failed to send log: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error streaming log: {e}")
        return False

def stream_logs_with_rate(logs: List[Dict[str, Any]], rate_per_second: int = 3, duration_seconds: int = 30):
    """Stream logs at a specified rate for a specified duration"""
    print(f"🚀 Starting log streaming...")
    print(f"   📊 Rate: {rate_per_second} logs/second")
    print(f"   ⏱️  Duration: {duration_seconds} seconds")
    print(f"   📝 Total logs: {len(logs)}")
    
    start_time = time.time()
    sent_count = 0
    log_index = 0
    
    while time.time() - start_time < duration_seconds:
        # Send logs at the specified rate
        for _ in range(rate_per_second):
            if log_index >= len(logs):
                log_index = 0  # Cycle through logs
            
            log = logs[log_index]
            log_index += 1
            
            # Add streaming metadata
            log['stream_metadata'] = {
                'streamed_at': datetime.utcnow().isoformat(),
                'stream_sequence': sent_count,
                'producer_id': 'sre-app-direct-streamer',
                'source': 'sre-application'
            }
            
            if stream_log_to_kafka(log):
                sent_count += 1
                print(f"✅ Sent log {sent_count}: {log['service']} - {log['level']}")
            else:
                print(f"❌ Failed to send log {sent_count + 1}")
        
        # Wait for the next second
        time.sleep(1)
    
    print(f"\n🎉 Streaming completed!")
    print(f"   📤 Total sent: {sent_count} logs")
    print(f"   ⏱️  Duration: {time.time() - start_time:.1f} seconds")
    print(f"   📊 Average rate: {sent_count / (time.time() - start_time):.1f} logs/second")

def main():
    """Main function"""
    print("🎬 SRE Application - Direct Log Streaming")
    print("=" * 50)
    
    # Load application logs
    logs = load_application_logs()
    
    if not logs:
        print("❌ No logs found to stream!")
        return False
    
    print(f"📊 Loaded {len(logs)} logs from your application")
    
    # Stream logs
    stream_logs_with_rate(logs, rate_per_second=3, duration_seconds=30)
    
    print("\n🎯 Check your Kafka UI at http://localhost:8081")
    print("   Navigate to Topics → system-logs → Messages")
    print("   You should see your application logs streaming in real-time!")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
