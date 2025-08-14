"""
Direct ML Model Test
===================
Test the ML model directly without Kafka
"""

import asyncio
from datetime import datetime
from sre_agent_orchestrator import LogEntry
from agents.anomaly_detector_agent import AnomalyDetectorAgent

async def test_ml_model():
    """Test the ML model directly"""
    print("🧪 Testing ML Model Directly")
    print("=" * 50)
    
    # Initialize the ML agent
    agent = AnomalyDetectorAgent()
    
    # Test 1: Normal log
    normal_log = LogEntry(
        timestamp=datetime.now().isoformat(),
        service="api-gateway",
        level="INFO",
        request_id="test_normal_001",
        host="test-host",
        environment="production",
        metrics={
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
        anomaly=False,
        message="Request processed successfully"
    )
    
    print("📊 Test 1: Normal log analysis...")
    result = await agent.analyze(normal_log)
    print(f"   Decision: {result['decision']}")
    print(f"   Confidence: {result['confidence']:.3f}")
    print(f"   Model Used: {result['metadata']['model_used']}")
    print(f"   Reasoning: {result['reasoning']}")
    
    # Test 2: High resource anomaly
    anomaly_log = LogEntry(
        timestamp=datetime.now().isoformat(),
        service="database-primary",
        level="ERROR",
        request_id="test_anomaly_001",
        host="test-host",
        environment="production",
        metrics={
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
        anomaly=True,
        message="Database connection pool exhausted"
    )
    
    print("\n📊 Test 2: Anomaly log analysis...")
    result = await agent.analyze(anomaly_log)
    print(f"   Decision: {result['decision']}")
    print(f"   Confidence: {result['confidence']:.3f}")
    print(f"   Model Used: {result['metadata']['model_used']}")
    print(f"   Reasoning: {result['reasoning']}")
    
    # Test 3: Edge case
    edge_log = LogEntry(
        timestamp=datetime.now().isoformat(),
        service="cache-service",
        level="INFO",
        request_id="test_edge_001",
        host="test-host",
        environment="production",
        metrics={
            "cpu_usage": 75.0,
            "memory_usage": 82.0,
            "disk_usage": 65.0,
            "network_in_mbps": 40.0,
            "network_out_mbps": 35.0,
            "active_connections": 400,
            "request_latency_ms": 500,
            "requests_per_second": 300,
            "error_rate": 0.08
        },
        anomaly=False,
        message="Cache hit ratio declining"
    )
    
    print("\n📊 Test 3: Edge case analysis...")
    result = await agent.analyze(edge_log)
    print(f"   Decision: {result['decision']}")
    print(f"   Confidence: {result['confidence']:.3f}")
    print(f"   Model Used: {result['metadata']['model_used']}")
    print(f"   Reasoning: {result['reasoning']}")
    
    print("\n" + "=" * 50)
    print("🎯 ML Model Test Results:")
    print("   - If 'ML Model' is shown, the trained model is being used")
    print("   - If 'Threshold Detection' is shown, fallback is being used")
    print("   - Confidence scores should vary based on anomaly severity")
    
    await agent.shutdown()

if __name__ == "__main__":
    asyncio.run(test_ml_model()) 