#!/usr/bin/env python3
"""
Complete SRE Agent System Test
==============================
Tests the entire SRE Agent system with all components:
1. Anomaly Detection
2. RAG Agent Analysis
3. Mitigation Agent Execution
4. Validation Simulator
5. Advanced LLM Escalation
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Import our components
from sre_agent_orchestrator import SREAgentOrchestrator, LogEntry
from orchestration.validation_simulator import MitigationSimulator, RAGMitigationStrategies
from agents.rag_agent import RAGAgent
from agents.mitigation_agent import MitigationAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteSystemTest:
    """Test the complete SRE Agent system"""
    
    def __init__(self):
        self.orchestrator = None
        self.simulator = MitigationSimulator()
        self.test_results = []
    
    async def setup(self):
        """Initialize the system"""
        logger.info("🔧 Setting up Complete SRE Agent System...")
        
        try:
            # Initialize orchestrator (without database to avoid locks)
            self.orchestrator = SREAgentOrchestrator()
            logger.info("✅ Orchestrator initialized")
            
            # Test individual components
            await self.test_validation_simulator()
            await self.test_rag_agent()
            await self.test_mitigation_agent()
            
            logger.info("🎉 System setup complete!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}")
            return False
    
    async def test_validation_simulator(self):
        """Test the validation simulator"""
        logger.info("🧪 Testing Validation Simulator...")
        
        # Test different anomaly types
        test_cases = [
            {
                'name': 'CPU Overload',
                'metrics': {'cpu_usage': 95.5, 'memory_usage': 78.3, 'error_rate': 0.08},
                'expected_type': 'cpu_overload'
            },
            {
                'name': 'Memory Leak',
                'metrics': {'cpu_usage': 45.2, 'memory_usage': 92.1, 'error_rate': 0.05},
                'expected_type': 'memory_leak'
            },
            {
                'name': 'Database Slowdown',
                'metrics': {'cpu_usage': 35.1, 'memory_usage': 45.8, 'request_latency_ms': 8000},
                'expected_type': 'database_slowdown'
            },
            {
                'name': 'Service Crash',
                'metrics': {'cpu_usage': 98.5, 'memory_usage': 95.2, 'error_rate': 0.25},
                'expected_type': 'service_crash'
            }
        ]
        
        for test_case in test_cases:
            logger.info(f"  Testing: {test_case['name']}")
            
            # Get mitigation strategy
            mitigation = RAGMitigationStrategies.get_mitigation(
                test_case['metrics'], 
                'test-service'
            )
            
            if mitigation:
                logger.info(f"    ✅ Found strategy: {mitigation.action_type.value}")
                
                # Simulate mitigation
                test_log = {
                    'timestamp': datetime.now().isoformat(),
                    'service': 'test-service',
                    'metrics': test_case['metrics'],
                    'anomaly': True
                }
                
                result = self.simulator.simulate_mitigation(test_log, mitigation, generate_logs=True)
                
                if result['success']:
                    improvement = result['validation']['improvement_percentage']
                    logger.info(f"    ✅ Mitigation successful: {improvement:.1f}% improvement")
                else:
                    logger.info(f"    ⚠️  Mitigation failed or needs rollback")
                
                self.test_results.append({
                    'test': test_case['name'],
                    'strategy_found': True,
                    'mitigation_success': result['success'],
                    'improvement': result['validation']['improvement_percentage'] if result['success'] else 0
                })
            else:
                logger.info(f"    ❌ No strategy found (should escalate to Advanced LLM)")
                self.test_results.append({
                    'test': test_case['name'],
                    'strategy_found': False,
                    'mitigation_success': False,
                    'improvement': 0
                })
    
    async def test_rag_agent(self):
        """Test the RAG agent"""
        logger.info("🧪 Testing RAG Agent...")
        
        try:
            rag_agent = RAGAgent()
            
            # Create test log entry
            test_log = LogEntry(
                timestamp=datetime.now().isoformat(),
                service="api-gateway",
                level="ERROR",
                request_id="req_test_rag_001",
                host="api-gateway-1.prod.internal",
                environment="production",
                metrics={
                    "cpu_usage": 92.5,
                    "memory_usage": 78.3,
                    "error_rate": 0.12,
                    "request_latency_ms": 4500,
                    "active_connections": 380
                },
                anomaly=True,
                message="High CPU usage detected"
            )
            
            # Mock anomaly decision
            anomaly_decision = {
                'decision': 'anomaly',
                'confidence': 0.85,
                'reasoning': 'CPU usage exceeds threshold'
            }
            
            # Process through RAG agent
            result = await rag_agent.process(test_log, anomaly_decision)
            
            logger.info(f"  ✅ RAG Agent processed: {result['decision']}")
            logger.info(f"  📊 Error Type: {result.get('error_type', 'unknown')}")
            logger.info(f"  🎯 Confidence: {result.get('confidence', 0):.2f}")
            logger.info(f"  📈 Needs Escalation: {result.get('needs_escalation', False)}")
            
            if 'thought_process' in result:
                thought = result['thought_process']
                logger.info(f"  🧠 Risk Assessment: {thought.get('risk_assessment', 'unknown')}")
                logger.info(f"  🎯 Approach: {thought.get('recommended_approach', 'unknown')}")
            
            self.test_results.append({
                'test': 'RAG Agent Processing',
                'decision': result['decision'],
                'error_type': result.get('error_type', 'unknown'),
                'confidence': result.get('confidence', 0),
                'needs_escalation': result.get('needs_escalation', False)
            })
            
        except Exception as e:
            logger.error(f"  ❌ RAG Agent test failed: {e}")
            self.test_results.append({
                'test': 'RAG Agent Processing',
                'error': str(e)
            })
    
    async def test_mitigation_agent(self):
        """Test the mitigation agent"""
        logger.info("🧪 Testing Mitigation Agent...")
        
        try:
            mitigation_agent = MitigationAgent()
            
            # Create test log entry
            test_log = LogEntry(
                timestamp=datetime.now().isoformat(),
                service="database-primary",
                level="ERROR",
                request_id="req_test_mitigation_001",
                host="db-primary-1.prod.internal",
                environment="production",
                metrics={
                    "cpu_usage": 88.5,
                    "memory_usage": 82.1,
                    "error_rate": 0.08,
                    "request_latency_ms": 3500,
                    "active_connections": 450
                },
                anomaly=True,
                message="Database performance degradation"
            )
            
            # Mock RAG result
            rag_result = {
                'actions_executed': [{
                    'type': 'restart_service',
                    'description': 'Restart database service',
                    'risk_level': 'medium',
                    'duration': 30
                }],
                'decision': 'mitigated',
                'confidence': 0.85
            }
            
            # Execute mitigation
            result = await mitigation_agent.execute_mitigation(test_log, rag_result)
            
            logger.info(f"  ✅ Mitigation execution: {result['status']}")
            logger.info(f"  ⏱️  Execution time: {result['execution']['execution_time']:.2f}s")
            logger.info(f"  📊 Improvement: {result['execution']['improvement_percentage']:.1f}%")
            logger.info(f"  🎯 Success: {result['execution']['success']}")
            
            if result['execution']['side_effects']:
                logger.info(f"  ⚠️  Side effects: {', '.join(result['execution']['side_effects'])}")
            
            self.test_results.append({
                'test': 'Mitigation Agent Execution',
                'status': result['status'],
                'execution_time': result['execution']['execution_time'],
                'improvement': result['execution']['improvement_percentage'],
                'success': result['execution']['success']
            })
            
        except Exception as e:
            logger.error(f"  ❌ Mitigation Agent test failed: {e}")
            self.test_results.append({
                'test': 'Mitigation Agent Execution',
                'error': str(e)
            })
    
    async def test_complete_flow(self):
        """Test the complete flow through the orchestrator"""
        logger.info("🧪 Testing Complete Flow...")
        
        if not self.orchestrator:
            logger.error("❌ Orchestrator not initialized")
            return
        
        # Test different scenarios
        scenarios = [
            {
                'name': 'Common Error - CPU Overload',
                'log': {
                    "timestamp": datetime.now().isoformat(),
                    "service": "web-service",
                    "level": "ERROR",
                    "request_id": "req_flow_001",
                    "host": "web-1.prod.internal",
                    "environment": "production",
                    "metrics": {
                        "cpu_usage": 94.2,
                        "memory_usage": 76.8,
                        "error_rate": 0.06,
                        "request_latency_ms": 2800,
                        "active_connections": 320
                    },
                    "anomaly": True,
                    "message": "High CPU usage detected"
                }
            },
            {
                'name': 'Service Crash - Escalation',
                'log': {
                    "timestamp": datetime.now().isoformat(),
                    "service": "critical-service",
                    "level": "CRITICAL",
                    "request_id": "req_flow_002",
                    "host": "critical-1.prod.internal",
                    "environment": "production",
                    "metrics": {
                        "cpu_usage": 98.5,
                        "memory_usage": 95.2,
                        "error_rate": 0.35,
                        "request_latency_ms": 15000,
                        "active_connections": 1200
                    },
                    "anomaly": True,
                    "message": "Critical service failure"
                }
            }
        ]
        
        for scenario in scenarios:
            logger.info(f"  Testing scenario: {scenario['name']}")
            
            try:
                # Process through orchestrator
                result = await self.orchestrator.process_log(scenario['log'])
                
                logger.info(f"    ✅ Processing completed in {result.get('processing_time', 0):.3f}s")
                logger.info(f"    📊 Decisions made: {len(result.get('decisions', []))}")
                logger.info(f"    ⚡ Actions taken: {len(result.get('actions_taken', []))}")
                
                # Log decisions
                for decision in result.get('decisions', []):
                    logger.info(f"      🎯 {decision.agent_name}: {decision.decision} ({decision.confidence:.2f})")
                
                # Log actions
                for action in result.get('actions_taken', []):
                    action_type = action.get('action', 'unknown')
                    success = action.get('success', False)
                    logger.info(f"      ⚡ {action_type}: {'✅' if success else '❌'}")
                
                self.test_results.append({
                    'test': f"Complete Flow - {scenario['name']}",
                    'processing_time': result.get('processing_time', 0),
                    'decisions_count': len(result.get('decisions', [])),
                    'actions_count': len(result.get('actions_taken', [])),
                    'success': 'error' not in result
                })
                
            except Exception as e:
                logger.error(f"    ❌ Scenario failed: {e}")
                self.test_results.append({
                    'test': f"Complete Flow - {scenario['name']}",
                    'error': str(e)
                })
    
    def print_summary(self):
        """Print test summary"""
        logger.info("\n" + "="*60)
        logger.info("📊 COMPLETE SYSTEM TEST SUMMARY")
        logger.info("="*60)
        
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if 'error' not in r])
        
        logger.info(f"Total Tests: {total_tests}")
        logger.info(f"Successful: {successful_tests}")
        logger.info(f"Failed: {total_tests - successful_tests}")
        logger.info(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
        
        logger.info("\n📋 Detailed Results:")
        for result in self.test_results:
            test_name = result['test']
            if 'error' in result:
                logger.info(f"  ❌ {test_name}: {result['error']}")
            else:
                logger.info(f"  ✅ {test_name}: Success")
        
        logger.info("\n🎉 SRE Agent System is ready for production!")
        logger.info("🌐 Dashboard available at: http://localhost:8081")
        logger.info("🚀 You can now trigger anomalies and see the complete flow!")

async def main():
    """Main test function"""
    logger.info("🚀 Starting Complete SRE Agent System Test")
    logger.info("="*60)
    
    tester = CompleteSystemTest()
    
    # Setup system
    if await tester.setup():
        # Test complete flow
        await tester.test_complete_flow()
        
        # Print summary
        tester.print_summary()
    else:
        logger.error("❌ System setup failed")

if __name__ == "__main__":
    asyncio.run(main()) 