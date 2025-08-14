"""
Test SRE Agent System
=====================
Comprehensive test script for the Intelligent SRE Agent system.
This script demonstrates various scenarios and validates the system functionality.
"""

import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Import our SRE Agent components
from sre_agent_orchestrator import SREAgentOrchestrator, LogEntry, LogSeverity
from agents.anomaly_detector_agent import AnomalyDetectorAgent
from agents.mitigation_agent import MitigationAgent
from agents.rag_agent import RAGAgent
from agents.advanced_llm_agent import AdvancedLLMAgent
from agents.database_agent import DatabaseAgent
from agents.paging_agent import PagingAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SREAgentSystemTester:
    """
    Comprehensive tester for the SRE Agent system
    """
    
    def __init__(self):
        """Initialize the tester"""
        self.orchestrator = None
        self.test_results = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'test_details': []
        }
        
        # Create test directories
        Path('logs').mkdir(exist_ok=True)
        Path('data').mkdir(exist_ok=True)
        
        logger.info("✅ SRE Agent System Tester initialized")
    
    async def run_all_tests(self):
        """Run all system tests"""
        print("\n" + "="*60)
        print("🧪 SRE AGENT SYSTEM COMPREHENSIVE TEST SUITE")
        print("="*60)
        
        try:
            # Initialize orchestrator
            await self._test_orchestrator_initialization()
            
            # Test individual agents
            await self._test_anomaly_detection_agent()
            await self._test_mitigation_agent()
            await self._test_rag_agent()
            await self._test_advanced_llm_agent()
            await self._test_database_agent()
            await self._test_paging_agent()
            
            # Test complete pipeline scenarios
            await self._test_normal_log_scenario()
            await self._test_common_error_scenario()
            await self._test_uncommon_error_scenario()
            await self._test_critical_incident_scenario()
            
            # Test system statistics and monitoring
            await self._test_system_statistics()
            
            # Print final results
            self._print_test_results()
            
        except Exception as e:
            logger.error(f"Test suite failed: {e}")
            self._record_test_result("Test Suite", False, f"Suite failed: {e}")
        finally:
            # Cleanup
            if self.orchestrator:
                await self.orchestrator.shutdown()
    
    async def _test_orchestrator_initialization(self):
        """Test orchestrator initialization"""
        test_name = "Orchestrator Initialization"
        
        try:
            self.orchestrator = SREAgentOrchestrator()
            
            # Check if all agents are initialized
            agent_count = len(self.orchestrator.agents)
            expected_agents = 6  # anomaly, mitigation, rag, llm, database, paging
            
            if agent_count == expected_agents:
                self._record_test_result(test_name, True, f"All {agent_count} agents initialized")
            else:
                self._record_test_result(test_name, False, f"Expected {expected_agents} agents, got {agent_count}")
                
        except Exception as e:
            self._record_test_result(test_name, False, f"Initialization failed: {e}")
    
    async def _test_anomaly_detection_agent(self):
        """Test anomaly detection agent"""
        test_name = "Anomaly Detection Agent"
        
        try:
            agent = self.orchestrator.agents.get("anomaly_detector")
            if not agent:
                self._record_test_result(test_name, False, "Agent not found")
                return
            
            # Test with normal log
            normal_log = LogEntry(
                timestamp="2025-08-12T17:09:17.944835",
                service="test-service",
                level="INFO",
                request_id="req_normal_001",
                host="test-host",
                environment="production",
                metrics={
                    "cpu_usage": 45.5,
                    "memory_usage": 67.2,
                    "disk_usage": 45.1,
                    "network_in_mbps": 50.0,
                    "network_out_mbps": 25.0,
                    "active_connections": 500,
                    "request_latency_ms": 200,
                    "requests_per_second": 100,
                    "error_rate": 0.01
                },
                anomaly=False,
                message="Normal operation"
            )
            
            result = await agent.analyze(normal_log)
            
            if result['decision'] == 'normal':
                self._record_test_result(test_name, True, "Normal log correctly classified")
            else:
                self._record_test_result(test_name, False, f"Normal log misclassified as {result['decision']}")
                
        except Exception as e:
            self._record_test_result(test_name, False, f"Test failed: {e}")
    
    async def _test_mitigation_agent(self):
        """Test mitigation agent"""
        test_name = "Mitigation Agent"
        
        try:
            agent = self.orchestrator.agents.get("mitigation")
            if not agent:
                self._record_test_result(test_name, False, "Agent not found")
                return
            
            # Test with common error
            common_error_log = LogEntry(
                timestamp="2025-08-12T17:09:17.944835",
                service="database-primary",
                level="ERROR",
                request_id="req_common_001",
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
            
            # Create mock anomaly decision
            from agents.anomaly_detector_agent import AgentDecision
            anomaly_decision = AgentDecision(
                agent_name="anomaly_detector",
                decision="anomaly",
                confidence=0.85,
                reasoning="High CPU and error rate detected",
                timestamp=datetime.now().isoformat(),
                metadata={}
            )
            
            result = await agent.analyze(common_error_log, anomaly_decision)
            
            if result['decision'] in ['common_error', 'uncommon_error']:
                self._record_test_result(test_name, True, f"Error correctly classified as {result['decision']}")
            else:
                self._record_test_result(test_name, False, f"Error misclassified as {result['decision']}")
                
        except Exception as e:
            self._record_test_result(test_name, False, f"Test failed: {e}")
    
    async def _test_rag_agent(self):
        """Test RAG agent"""
        test_name = "RAG Agent"
        
        try:
            agent = self.orchestrator.agents.get("rag")
            if not agent:
                self._record_test_result(test_name, False, "Agent not found")
                return
            
            # Test with common error scenario
            common_error_log = LogEntry(
                timestamp="2025-08-12T17:09:17.944835",
                service="database-primary",
                level="ERROR",
                request_id="req_rag_001",
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
            
            # Create mock decisions
            from agents.anomaly_detector_agent import AgentDecision
            anomaly_decision = AgentDecision(
                agent_name="anomaly_detector",
                decision="anomaly",
                confidence=0.85,
                reasoning="High CPU and error rate detected",
                timestamp=datetime.now().isoformat(),
                metadata={}
            )
            
            mitigation_decision = AgentDecision(
                agent_name="mitigation",
                decision="common_error",
                confidence=0.9,
                reasoning="Matches known connection pool pattern",
                timestamp=datetime.now().isoformat(),
                metadata={'error_type': 'connection_pool_exhausted'}
            )
            
            result = await agent.process(common_error_log, anomaly_decision, mitigation_decision)
            
            if result.get('agent') == 'rag_agent':
                self._record_test_result(test_name, True, f"RAG agent processed successfully: {result.get('error_type', 'unknown')}")
            else:
                self._record_test_result(test_name, False, f"RAG agent failed: {result}")
                
        except Exception as e:
            self._record_test_result(test_name, False, f"Test failed: {e}")
    
    async def _test_advanced_llm_agent(self):
        """Test advanced LLM agent"""
        test_name = "Advanced LLM Agent"
        
        try:
            agent = self.orchestrator.agents.get("advanced_llm")
            if not agent:
                self._record_test_result(test_name, False, "Agent not found")
                return
            
            # Test with uncommon error scenario
            uncommon_error_log = LogEntry(
                timestamp="2025-08-12T17:09:17.944835",
                service="custom-service",
                level="CRITICAL",
                request_id="req_llm_001",
                host="test-host",
                environment="production",
                metrics={
                    "cpu_usage": 98.5,
                    "memory_usage": 92.2,
                    "disk_usage": 45.1,
                    "network_in_mbps": 200.0,
                    "network_out_mbps": 50.0,
                    "active_connections": 1500,
                    "request_latency_ms": 8000,
                    "requests_per_second": 25,
                    "error_rate": 0.25
                },
                anomaly=True,
                message="Unknown critical error in custom service"
            )
            
            # Create mock decisions
            from agents.anomaly_detector_agent import AgentDecision
            anomaly_decision = AgentDecision(
                agent_name="anomaly_detector",
                decision="anomaly",
                confidence=0.95,
                reasoning="Critical error with high CPU and memory usage",
                timestamp=datetime.now().isoformat(),
                metadata={}
            )
            
            mitigation_decision = AgentDecision(
                agent_name="mitigation",
                decision="uncommon_error",
                confidence=0.3,
                reasoning="Unknown error pattern",
                timestamp=datetime.now().isoformat(),
                metadata={'error_type': 'unknown'}
            )
            
            result = await agent.process(uncommon_error_log, anomaly_decision, mitigation_decision)
            
            if result.get('agent') == 'advanced_llm_agent':
                analysis = result.get('analysis', {})
                self._record_test_result(test_name, True, f"LLM analysis completed: {analysis.get('severity', 'unknown')} severity")
            else:
                self._record_test_result(test_name, False, f"LLM agent failed: {result}")
                
        except Exception as e:
            self._record_test_result(test_name, False, f"Test failed: {e}")
    
    async def _test_database_agent(self):
        """Test database agent"""
        test_name = "Database Agent"
        
        try:
            agent = self.orchestrator.agents.get("database")
            if not agent:
                self._record_test_result(test_name, False, "Agent not found")
                return
            
            # Test storing a log
            test_log = LogEntry(
                timestamp="2025-08-12T17:09:17.944835",
                service="test-service",
                level="INFO",
                request_id="req_db_001",
                host="test-host",
                environment="production",
                metrics={
                    "cpu_usage": 45.5,
                    "memory_usage": 67.2,
                    "disk_usage": 45.1,
                    "network_in_mbps": 50.0,
                    "network_out_mbps": 25.0,
                    "active_connections": 500,
                    "request_latency_ms": 200,
                    "requests_per_second": 100,
                    "error_rate": 0.01
                },
                anomaly=False,
                message="Normal operation"
            )
            
            result = await agent.store_log(test_log)
            
            if result['success']:
                self._record_test_result(test_name, True, "Log stored successfully")
            else:
                self._record_test_result(test_name, False, f"Log storage failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self._record_test_result(test_name, False, f"Test failed: {e}")
    
    async def _test_paging_agent(self):
        """Test paging agent"""
        test_name = "Paging Agent"
        
        try:
            agent = self.orchestrator.agents.get("paging")
            if not agent:
                self._record_test_result(test_name, False, "Agent not found")
                return
            
            # Test with critical incident
            critical_log = LogEntry(
                timestamp="2025-08-12T17:09:17.944835",
                service="critical-service",
                level="CRITICAL",
                request_id="req_page_001",
                host="test-host",
                environment="production",
                metrics={
                    "cpu_usage": 98.5,
                    "memory_usage": 92.2,
                    "disk_usage": 45.1,
                    "network_in_mbps": 200.0,
                    "network_out_mbps": 50.0,
                    "active_connections": 1500,
                    "request_latency_ms": 8000,
                    "requests_per_second": 25,
                    "error_rate": 0.25
                },
                anomaly=True,
                message="Critical system failure"
            )
            
            llm_result = {
                'analysis': {
                    'root_cause': 'Memory exhaustion and high CPU usage',
                    'severity': 'critical',
                    'impact': 'Service unavailability',
                    'confidence': 0.9
                },
                'recommendations': {
                    'actions': [
                        'Immediately restart the service',
                        'Scale up resources',
                        'Investigate memory leak'
                    ],
                    'commands': [
                        'sudo systemctl restart critical-service',
                        'kubectl scale deployment critical-service --replicas=3'
                    ]
                },
                'escalation': {
                    'required': True,
                    'urgency': 'high',
                    'recipients': ['oncall-sre@company.com'],
                    'timeframe': 'immediate',
                    'instructions': 'Immediate action required'
                }
            }
            
            result = await agent.send_page(critical_log, llm_result)
            
            if result.get('success'):
                self._record_test_result(test_name, True, f"Page sent successfully: {result.get('urgency', 'unknown')} urgency")
            else:
                self._record_test_result(test_name, False, f"Page failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self._record_test_result(test_name, False, f"Test failed: {e}")
    
    async def _test_normal_log_scenario(self):
        """Test complete pipeline with normal log"""
        test_name = "Normal Log Pipeline"
        
        try:
            normal_log_data = {
                "timestamp": "2025-08-12T17:09:17.944835",
                "service": "test-service",
                "level": "INFO",
                "request_id": "req_normal_pipeline_001",
                "host": "test-host",
                "environment": "production",
                "metrics": {
                    "cpu_usage": 45.5,
                    "memory_usage": 67.2,
                    "disk_usage": 45.1,
                    "network_in_mbps": 50.0,
                    "network_out_mbps": 25.0,
                    "active_connections": 500,
                    "request_latency_ms": 200,
                    "requests_per_second": 100,
                    "error_rate": 0.01
                },
                "anomaly": False,
                "message": "Normal operation"
            }
            
            result = await self.orchestrator.process_log(normal_log_data)
            
            if not result.get('error'):
                decisions = result.get('decisions', [])
                if decisions and decisions[0].decision == 'normal':
                    self._record_test_result(test_name, True, "Normal log processed correctly through pipeline")
                else:
                    self._record_test_result(test_name, False, f"Normal log misclassified: {decisions}")
            else:
                self._record_test_result(test_name, False, f"Pipeline failed: {result['error']}")
                
        except Exception as e:
            self._record_test_result(test_name, False, f"Test failed: {e}")
    
    async def _test_common_error_scenario(self):
        """Test complete pipeline with common error"""
        test_name = "Common Error Pipeline"
        
        try:
            common_error_data = {
                "timestamp": "2025-08-12T17:09:17.944835",
                "service": "database-primary",
                "level": "ERROR",
                "request_id": "req_common_pipeline_001",
                "host": "test-host",
                "environment": "production",
                "metrics": {
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
                "anomaly": True,
                "message": "Database connection pool exhausted"
            }
            
            result = await self.orchestrator.process_log(common_error_data)
            
            if not result.get('error'):
                actions = result.get('actions_taken', [])
                rag_action = next((a for a in actions if a.get('agent') == 'rag_agent'), None)
                
                if rag_action:
                    self._record_test_result(test_name, True, f"Common error handled by RAG agent: {rag_action.get('error_type', 'unknown')}")
                else:
                    self._record_test_result(test_name, False, "Common error not handled by RAG agent")
            else:
                self._record_test_result(test_name, False, f"Pipeline failed: {result['error']}")
                
        except Exception as e:
            self._record_test_result(test_name, False, f"Test failed: {e}")
    
    async def _test_uncommon_error_scenario(self):
        """Test complete pipeline with uncommon error"""
        test_name = "Uncommon Error Pipeline"
        
        try:
            uncommon_error_data = {
                "timestamp": "2025-08-12T17:09:17.944835",
                "service": "custom-service",
                "level": "CRITICAL",
                "request_id": "req_uncommon_pipeline_001",
                "host": "test-host",
                "environment": "production",
                "metrics": {
                    "cpu_usage": 98.5,
                    "memory_usage": 92.2,
                    "disk_usage": 45.1,
                    "network_in_mbps": 200.0,
                    "network_out_mbps": 50.0,
                    "active_connections": 1500,
                    "request_latency_ms": 8000,
                    "requests_per_second": 25,
                    "error_rate": 0.25
                },
                "anomaly": True,
                "message": "Unknown critical error in custom service"
            }
            
            result = await self.orchestrator.process_log(uncommon_error_data)
            
            if not result.get('error'):
                actions = result.get('actions_taken', [])
                llm_action = next((a for a in actions if a.get('agent') == 'advanced_llm_agent'), None)
                paging_action = next((a for a in actions if a.get('agent') == 'paging_agent'), None)
                
                if llm_action and paging_action:
                    self._record_test_result(test_name, True, "Uncommon error handled by LLM agent and paging sent")
                else:
                    self._record_test_result(test_name, False, "Uncommon error not handled correctly")
            else:
                self._record_test_result(test_name, False, f"Pipeline failed: {result['error']}")
                
        except Exception as e:
            self._record_test_result(test_name, False, f"Test failed: {e}")
    
    async def _test_critical_incident_scenario(self):
        """Test complete pipeline with critical incident"""
        test_name = "Critical Incident Pipeline"
        
        try:
            critical_incident_data = {
                "timestamp": "2025-08-12T17:09:17.944835",
                "service": "production-api",
                "level": "CRITICAL",
                "request_id": "req_critical_pipeline_001",
                "host": "prod-api-01",
                "environment": "production",
                "metrics": {
                    "cpu_usage": 99.9,
                    "memory_usage": 99.5,
                    "disk_usage": 95.1,
                    "network_in_mbps": 500.0,
                    "network_out_mbps": 100.0,
                    "active_connections": 5000,
                    "request_latency_ms": 15000,
                    "requests_per_second": 5,
                    "error_rate": 0.8
                },
                "anomaly": True,
                "message": "Complete system failure - all services down"
            }
            
            result = await self.orchestrator.process_log(critical_incident_data)
            
            if not result.get('error'):
                actions = result.get('actions_taken', [])
                paging_action = next((a for a in actions if a.get('agent') == 'paging_agent'), None)
                
                if paging_action and paging_action.get('urgency') == 'high':
                    self._record_test_result(test_name, True, "Critical incident escalated with high urgency paging")
                else:
                    self._record_test_result(test_name, False, "Critical incident not escalated properly")
            else:
                self._record_test_result(test_name, False, f"Pipeline failed: {result['error']}")
                
        except Exception as e:
            self._record_test_result(test_name, False, f"Test failed: {e}")
    
    async def _test_system_statistics(self):
        """Test system statistics and monitoring"""
        test_name = "System Statistics"
        
        try:
            # Get orchestrator stats
            orchestrator_stats = self.orchestrator.get_stats()
            
            # Get individual agent stats
            agent_stats = {}
            for agent_name, agent in self.orchestrator.agents.items():
                if hasattr(agent, 'get_stats'):
                    agent_stats[agent_name] = agent.get_stats()
            
            # Validate stats structure
            required_orchestrator_fields = ['total_logs_processed', 'anomalies_detected', 'common_errors', 'uncommon_errors']
            missing_fields = [field for field in required_orchestrator_fields if field not in orchestrator_stats]
            
            if not missing_fields:
                self._record_test_result(test_name, True, f"Statistics collected: {orchestrator_stats['total_logs_processed']} logs processed")
            else:
                self._record_test_result(test_name, False, f"Missing statistics fields: {missing_fields}")
                
        except Exception as e:
            self._record_test_result(test_name, False, f"Test failed: {e}")
    
    def _record_test_result(self, test_name: str, passed: bool, message: str):
        """Record a test result"""
        self.test_results['total_tests'] += 1
        
        if passed:
            self.test_results['passed_tests'] += 1
            status = "✅ PASS"
        else:
            self.test_results['failed_tests'] += 1
            status = "❌ FAIL"
        
        test_detail = {
            'name': test_name,
            'passed': passed,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        self.test_results['test_details'].append(test_detail)
        
        print(f"{status} {test_name}: {message}")
    
    def _print_test_results(self):
        """Print comprehensive test results"""
        print("\n" + "="*60)
        print("📊 TEST RESULTS SUMMARY")
        print("="*60)
        
        total = self.test_results['total_tests']
        passed = self.test_results['passed_tests']
        failed = self.test_results['failed_tests']
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "Success Rate: N/A")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for test in self.test_results['test_details']:
                if not test['passed']:
                    print(f"  - {test['name']}: {test['message']}")
        
        print("\n" + "="*60)
        
        # Save detailed results to file
        results_file = Path('logs/test_results.json')
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        print(f"Detailed results saved to: {results_file}")

async def main():
    """Main test function"""
    print("🧪 Starting SRE Agent System Tests...")
    print("This will test all components of the intelligent SRE agent system.")
    print("-" * 60)
    
    tester = SREAgentSystemTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main()) 