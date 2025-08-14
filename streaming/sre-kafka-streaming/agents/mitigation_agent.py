"""
Mitigation Agent
================
Agent that executes and validates mitigation actions using the validation simulator
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from orchestration.validation_simulator import (
    MitigationAction, ActionType, MitigationSimulator, 
    RAGMitigationStrategies, ValidationResult
)

logger = logging.getLogger(__name__)

@dataclass
class MitigationExecution:
    """Represents a mitigation execution"""
    action: MitigationAction
    validation_result: ValidationResult
    execution_time: float
    success: bool
    logs_generated: List[Dict[str, Any]]
    side_effects: List[str]

class MitigationAgent:
    """
    Mitigation Agent for executing and validating mitigation actions
    """
    
    def __init__(self):
        self.simulator = MitigationSimulator()
        self.stats = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'total_improvement': 0.0,
            'average_execution_time': 0.0
        }
        
        logger.info("✅ Mitigation Agent initialized with validation simulator")
    
    async def execute_mitigation(self, log_entry, rag_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute mitigation based on RAG agent recommendations
        
        Args:
            log_entry: LogEntry object
            rag_result: Result from RAG agent
            
        Returns:
            Execution result with validation and metrics
        """
        try:
            self.stats['total_executions'] += 1
            start_time = datetime.now()
            
            # Extract action from RAG result
            if 'actions_executed' not in rag_result or not rag_result['actions_executed']:
                return {
                    'status': 'no_actions',
                    'reason': 'No actions provided by RAG agent',
                    'execution_time': 0.0
                }
            
            # Get the first action (most important)
            action_data = rag_result['actions_executed'][0]
            
            # Convert to MitigationAction
            action = self._create_mitigation_action(action_data, log_entry.service)
            
            # Execute the mitigation
            logger.info(f"Executing mitigation: {action.action_type.value} for {action.service}")
            
            # Simulate execution time
            await asyncio.sleep(2)  # Simulate actual execution
            
            # Validate the action
            validation_result = self.simulator.validator.validate_action(action, {
                'service': log_entry.service,
                'metrics': log_entry.metrics
            })
            
            # Generate recovery logs if successful
            logs_generated = []
            if validation_result.success:
                logs_generated = self.simulator.log_generator.generate_fixed_logs(
                    service=action.service,
                    metrics=validation_result.metrics_after,
                    count=5,
                    interval_seconds=30
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Update statistics
            if validation_result.success:
                self.stats['successful_executions'] += 1
                self.stats['total_improvement'] += validation_result.improvement_percentage
            else:
                self.stats['failed_executions'] += 1
            
            self.stats['average_execution_time'] = (
                (self.stats['average_execution_time'] * (self.stats['total_executions'] - 1) + execution_time) 
                / self.stats['total_executions']
            )
            
            # Create execution result
            execution = MitigationExecution(
                action=action,
                validation_result=validation_result,
                execution_time=execution_time,
                success=validation_result.success,
                logs_generated=logs_generated,
                side_effects=validation_result.side_effects
            )
            
            result = {
                'status': 'success' if validation_result.success else 'failed',
                'execution': {
                    'action_type': action.action_type.value,
                    'service': action.service,
                    'execution_time': execution_time,
                    'success': validation_result.success,
                    'improvement_percentage': validation_result.improvement_percentage,
                    'time_to_effect': validation_result.time_to_effect,
                    'side_effects': validation_result.side_effects,
                    'logs_generated': len(logs_generated)
                },
                'metrics': {
                    'before': validation_result.metrics_before,
                    'after': validation_result.metrics_after,
                    'improvement': {
                        'cpu_reduction': validation_result.metrics_before.get('cpu_usage', 0) - 
                                        validation_result.metrics_after.get('cpu_usage', 0),
                        'memory_reduction': validation_result.metrics_before.get('memory_usage', 0) - 
                                           validation_result.metrics_after.get('memory_usage', 0),
                        'error_rate_reduction': validation_result.metrics_before.get('error_rate', 0) - 
                                               validation_result.metrics_after.get('error_rate', 0)
                    }
                },
                'recovery_logs': logs_generated,
                'needs_rollback': validation_result.rollback_needed
            }
            
            logger.info(f"Mitigation execution completed: {result['status']} ({execution_time:.2f}s)")
            return result
            
        except Exception as e:
            logger.error(f"Error in mitigation execution: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'execution_time': 0.0
            }
    
    def _create_mitigation_action(self, action_data: Dict[str, Any], service: str) -> MitigationAction:
        """Create MitigationAction from action data"""
        
        # Map action types
        action_type_map = {
            'restart_service': ActionType.RESTART_SERVICE,
            'scale_up': ActionType.SCALE_HORIZONTAL,
            'clear_cache': ActionType.CLEAR_CACHE,
            'kill_processes': ActionType.THROTTLE_REQUESTS,
            'update_config': ActionType.CIRCUIT_BREAKER,
            'rollback': ActionType.ROLLBACK_DEPLOYMENT
        }
        
        action_type = action_type_map.get(action_data.get('type', ''), ActionType.RESTART_SERVICE)
        
        return MitigationAction(
            action_type=action_type,
            service=service,
            parameters={
                'description': action_data.get('description', ''),
                'risk_level': action_data.get('risk_level', 'medium'),
                'duration': action_data.get('duration', 30)
            },
            confidence=0.85,  # Based on RAG recommendation
            source='rag',
            timestamp=datetime.now().isoformat(),
            expected_impact={
                'issue_type': 'mitigation_execution',
                'expected_resolution_time': action_data.get('duration', 30)
            }
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            **self.stats,
            'success_rate': self.stats['successful_executions'] / max(self.stats['total_executions'], 1),
            'average_improvement': self.stats['total_improvement'] / max(self.stats['successful_executions'], 1)
        }
    
    async def shutdown(self):
        """Cleanup resources"""
        logger.info("Mitigation Agent shutdown complete")

# Example usage
if __name__ == "__main__":
    import asyncio
    from sre_agent_orchestrator import LogEntry
    
    async def test_agent():
        agent = MitigationAgent()
        
        # Test log entry
        test_log = LogEntry(
            timestamp="2025-08-12T17:09:17.944835",
            service="database-primary",
            level="ERROR",
            request_id="req_test_001",
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
        
        # Mock RAG result
        rag_result = {
            'actions_executed': [{
                'type': 'restart_service',
                'description': 'Restart database service',
                'risk_level': 'medium',
                'duration': 30
            }]
        }
        
        result = await agent.execute_mitigation(test_log, rag_result)
        print(f"Execution result: {result}")
        
        stats = agent.get_stats()
        print(f"Agent stats: {stats}")
        
        await agent.shutdown()
    
    asyncio.run(test_agent())
