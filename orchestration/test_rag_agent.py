#!/usr/bin/env python3
"""
Test script for RAG Agent with OpenAI integration
"""

import asyncio
import json
from datetime import datetime
from agents.rag_agent import RAGAgent
from sre_agent_orchestrator import LogEntry, AgentDecision

async def test_rag_agent():
    """Test the RAG agent with a sample log entry"""
    
    # Create a test log entry
    test_log = LogEntry(
        timestamp=datetime.now().isoformat(),
        service="database-primary",
        level="ERROR",
        request_id="test_rag_001",
        host="test-host",
        environment="production",
        metrics={
            "cpu_usage": 95.5,
            "memory_usage": 87.2,
            "disk_usage": 45.1,
            "network_in_mbps": 150.0,
            "network_out_mbps": 25.0,
            "active_connections": 1200,
            "request_latency_ms": 5000,
            "requests_per_second": 50,
            "error_rate": 0.15
        },
        anomaly=True,
        message="Database connection pool exhausted"
    )
    
    # Create a test anomaly decision
    anomaly_decision = {
        'decision': 'anomaly',
        'confidence': 0.85,
        'reasoning': 'High CPU usage and error rate detected'
    }
    
    print("🧪 Testing RAG Agent with OpenAI integration...")
    print(f"📝 Test log: {test_log.service} - {test_log.level}")
    print(f"📊 Metrics: CPU={test_log.metrics['cpu_usage']}%, Memory={test_log.metrics['memory_usage']}%")
    
    try:
        # Initialize RAG agent
        rag_agent = RAGAgent()
        
        # Process the log
        print("\n🔄 Processing log through RAG agent...")
        result = await rag_agent.process(test_log, anomaly_decision)
        
        print("\n✅ RAG Agent Result:")
        print(json.dumps(result, indent=2))
        
        # Check if escalation is needed
        if result.get('needs_escalation', False):
            print("\n🚨 Escalation to Advanced LLM Agent required!")
        else:
            print("\n✅ Issue resolved by RAG Agent!")
        
        # Show agent stats
        stats = rag_agent.get_stats()
        print(f"\n📈 Agent Stats: {stats}")
        
    except Exception as e:
        print(f"\n❌ Error testing RAG agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_agent()) 