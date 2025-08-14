"""
Test ML Orchestrator Integration
=================================
Sends test logs (normal and anomalous) to verify ML detection is working
"""

import json
import subprocess
import time
from datetime import datetime

def send_log_to_kafka(log_data):
    """Send a log to Kafka using docker exec"""
    log_json = json.dumps(log_data)
    
    cmd = [
        "docker", "exec", "-i", "sre-kafka",
        "kafka-console-producer",
        "--bootstrap-server", "localhost:9093",
        "--topic", "system-logs"
    ]
    
    result = subprocess.run(
        cmd,
        input=log_json,
        capture_output=True,
        text=True,
        timeout=10
    )
    
    return result.returncode == 0

def test_ml_detection():
    """Send various test logs to test ML detection"""
    
    print("🧪 Testing ML Orchestrator Detection")
    print("=" * 50)
    
    # Test 1: Normal log (should NOT trigger anomaly)
    normal_log = {
        "timestamp": datetime.now().isoformat(),
        "service": "api-gateway",
        "level": "INFO",
        "message": "Request processed successfully",
        "metrics": {
            "cpu_usage": 45.0,
            "memory_usage": 50.0,
            "disk_usage": 60.0,
            "network_in_mbps": 50.0,
            "network_out_mbps": 45.0,
            "active_connections": 200,
            "request_latency_ms": 100,
            "requests_per_second": 500,
            "error_rate": 0.005
        },
        "anomaly": False  # Ground truth
    }
    
    print("📤 Test 1: Sending NORMAL log...")
    if send_log_to_kafka(normal_log):
        print("   ✅ Normal log sent (CPU: 45%, Memory: 50%)")
    else:
        print("   ❌ Failed to send")
    
    time.sleep(2)
    
    # Test 2: High resource anomaly (should trigger)
    high_resource_log = {
        "timestamp": datetime.now().isoformat(),
        "service": "database-primary",
        "level": "ERROR",
        "message": "Database connection pool exhausted",
        "metrics": {
            "cpu_usage": 92.5,
            "memory_usage": 88.3,
            "disk_usage": 75.0,
            "network_in_mbps": 10.0,
            "network_out_mbps": 8.0,
            "active_connections": 950,
            "request_latency_ms": 3500,
            "requests_per_second": 100,
            "error_rate": 0.25
        },
        "anomaly": True  # Ground truth
    }
    
    print("\n📤 Test 2: Sending HIGH RESOURCE ANOMALY...")
    if send_log_to_kafka(high_resource_log):
        print("   ✅ Anomaly log sent (CPU: 92.5%, Memory: 88.3%)")
    else:
        print("   ❌ Failed to send")
    
    time.sleep(2)
    
    # Test 3: High latency anomaly
    high_latency_log = {
        "timestamp": datetime.now().isoformat(),
        "service": "payment-service",
        "level": "WARNING",
        "message": "Payment processing slow",
        "metrics": {
            "cpu_usage": 65.0,
            "memory_usage": 70.0,
            "disk_usage": 50.0,
            "network_in_mbps": 30.0,
            "network_out_mbps": 25.0,
            "active_connections": 500,
            "request_latency_ms": 5000,  # Very high latency
            "requests_per_second": 50,
            "error_rate": 0.15
        },
        "anomaly": True  # Ground truth
    }
    
    print("\n📤 Test 3: Sending HIGH LATENCY ANOMALY...")
    if send_log_to_kafka(high_latency_log):
        print("   ✅ Anomaly log sent (Latency: 5000ms)")
    else:
        print("   ❌ Failed to send")
    
    time.sleep(2)
    
    # Test 4: Edge case - moderate metrics
    edge_case_log = {
        "timestamp": datetime.now().isoformat(),
        "service": "cache-service",
        "level": "INFO",
        "message": "Cache hit ratio declining",
        "metrics": {
            "cpu_usage": 75.0,  # Below threshold but high
            "memory_usage": 82.0,  # Close to threshold
            "disk_usage": 65.0,
            "network_in_mbps": 40.0,
            "network_out_mbps": 35.0,
            "active_connections": 400,
            "request_latency_ms": 500,
            "requests_per_second": 300,
            "error_rate": 0.08
        },
        "anomaly": False  # Ground truth (borderline case)
    }
    
    print("\n📤 Test 4: Sending EDGE CASE log...")
    if send_log_to_kafka(edge_case_log):
        print("   ✅ Edge case log sent (CPU: 75%, Memory: 82%)")
    else:
        print("   ❌ Failed to send")
    
    print("\n" + "=" * 50)
    print("🎯 Check the ML Orchestrator terminal to see:")
    print("   1. Normal log should NOT trigger anomaly")
    print("   2. High resource log should trigger HIGH confidence")
    print("   3. High latency log should trigger anomaly")
    print("   4. Edge case - see what ML model decides!")
    print("\n💡 ML model should provide better detection than simple thresholds")

if __name__ == "__main__":
    test_ml_detection()