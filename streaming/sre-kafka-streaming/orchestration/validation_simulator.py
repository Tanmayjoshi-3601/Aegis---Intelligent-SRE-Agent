"""
Validation and Simulation System for SRE Agent Actions
Simulates the effect of mitigation actions on logs
"""

import json
import time
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Types of mitigation actions"""
    RESTART_SERVICE = "restart_service"
    SCALE_HORIZONTAL = "scale_horizontal"
    SCALE_VERTICAL = "scale_vertical"
    CLEAR_CACHE = "clear_cache"
    INCREASE_CONNECTION_POOL = "increase_connection_pool"
    THROTTLE_REQUESTS = "throttle_requests"
    FAILOVER_DATABASE = "failover_database"
    ROLLBACK_DEPLOYMENT = "rollback_deployment"
    DRAIN_QUEUE = "drain_queue"
    CIRCUIT_BREAKER = "circuit_breaker"

@dataclass
class MitigationAction:
    """Represents a mitigation action"""
    action_type: ActionType
    service: str
    parameters: Dict[str, Any]
    confidence: float
    source: str  # 'rag' or 'llm'
    timestamp: str
    expected_impact: Dict[str, Any]

@dataclass
class ValidationResult:
    """Result of action validation"""
    action_id: str
    success: bool
    metrics_before: Dict[str, float]
    metrics_after: Dict[str, float]
    improvement_percentage: float
    time_to_effect: int  # seconds
    side_effects: List[str]
    rollback_needed: bool

class ServiceSimulator:
    """Simulates service behavior and metrics after actions"""
    
    def __init__(self):
        self.service_states = {}
        self.action_effects = self._define_action_effects()
        self.baseline_metrics = {
            'cpu_usage': 45.0,
            'memory_usage': 50.0,
            'error_rate': 0.001,
            'request_latency_ms': 100,
            'active_connections': 200
        }
        
    def _define_action_effects(self) -> Dict[ActionType, Dict[str, Any]]:
        """Define how each action affects metrics"""
        return {
            ActionType.RESTART_SERVICE: {
                'cpu_usage': lambda x: max(20, x * 0.4),  # Drops to 40% of original
                'memory_usage': lambda x: max(25, x * 0.3),  # Drops to 30%
                'error_rate': lambda x: x * 0.1,  # 90% reduction in errors
                'request_latency_ms': lambda x: x * 1.5,  # Temporary increase
                'time_to_effect': 30,
                'duration': 300,  # Effects last 5 minutes
                'side_effects': ['temporary_unavailability', 'connection_reset']
            },
            ActionType.SCALE_HORIZONTAL: {
                'cpu_usage': lambda x: x * 0.6,  # Distribute load
                'memory_usage': lambda x: x * 0.7,
                'request_latency_ms': lambda x: x * 0.8,
                'active_connections': lambda x: x * 0.5,  # Distribute connections
                'time_to_effect': 60,
                'duration': 3600,  # Effects last 1 hour
                'side_effects': ['increased_cost']
            },
            ActionType.CLEAR_CACHE: {
                'memory_usage': lambda x: x * 0.5,  # Free up memory
                'request_latency_ms': lambda x: x * 1.3,  # Cache miss penalty
                'time_to_effect': 5,
                'duration': 600,
                'side_effects': ['temporary_slow_responses']
            },
            ActionType.INCREASE_CONNECTION_POOL: {
                'active_connections': lambda x: min(x * 1.5, 500),
                'error_rate': lambda x: x * 0.5,  # Reduce connection errors
                'time_to_effect': 10,
                'duration': 3600,
                'side_effects': ['increased_memory_usage']
            },
            ActionType.THROTTLE_REQUESTS: {
                'cpu_usage': lambda x: x * 0.7,
                'request_latency_ms': lambda x: x * 0.9,
                'error_rate': lambda x: x * 1.2,  # Some requests rejected
                'time_to_effect': 5,
                'duration': 900,
                'side_effects': ['reduced_throughput', 'client_errors']
            },
            ActionType.CIRCUIT_BREAKER: {
                'error_rate': lambda x: x * 0.2,  # Prevent cascade
                'cpu_usage': lambda x: x * 0.8,
                'time_to_effect': 2,
                'duration': 600,
                'side_effects': ['partial_service_degradation']
            }
        }
    
    def simulate_action(self, action: MitigationAction, current_metrics: Dict[str, float]) -> Tuple[Dict[str, float], List[str]]:
        """Simulate the effect of an action on metrics"""
        
        effects = self.action_effects.get(action.action_type, {})
        new_metrics = current_metrics.copy()
        side_effects = effects.get('side_effects', [])
        
        # Apply metric changes
        for metric, transform in effects.items():
            if metric in new_metrics and callable(transform):
                new_metrics[metric] = transform(new_metrics[metric])
        
        # Add some randomness to simulate real-world variance
        for metric in new_metrics:
            if isinstance(new_metrics[metric], (int, float)):
                variance = random.uniform(0.95, 1.05)
                new_metrics[metric] *= variance
        
        return new_metrics, side_effects
    
    def get_service_state(self, service: str) -> Dict[str, Any]:
        """Get current state of a service"""
        if service not in self.service_states:
            self.service_states[service] = {
                'healthy': True,
                'metrics': self.baseline_metrics.copy(),
                'active_actions': [],
                'history': []
            }
        return self.service_states[service]
    
    def update_service_state(self, service: str, metrics: Dict[str, float]):
        """Update service state with new metrics"""
        state = self.get_service_state(service)
        state['metrics'] = metrics
        state['healthy'] = self._is_healthy(metrics)
        state['history'].append({
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics.copy()
        })

    def _is_healthy(self, metrics: Dict[str, float]) -> bool:
        """Determine if metrics indicate a healthy service"""
        return (
            metrics.get('cpu_usage', 0) < 80 and
            metrics.get('memory_usage', 0) < 85 and
            metrics.get('error_rate', 0) < 0.05 and
            metrics.get('request_latency_ms', 0) < 500
        )

class ActionValidator:
    """Validates mitigation actions and their effects"""
    
    def __init__(self):
        self.simulator = ServiceSimulator()
        self.validation_history = []
        
    def validate_action(self, action: MitigationAction, current_log: Dict[str, Any]) -> ValidationResult:
        """Validate a mitigation action by simulating its effects"""
        
        # Extract current metrics from log
        current_metrics = current_log.get('metrics', {})
        service = current_log.get('service', 'unknown')
        
        # Simulate the action
        new_metrics, side_effects = self.simulator.simulate_action(action, current_metrics)
        
        # Calculate improvement
        improvement = self._calculate_improvement(current_metrics, new_metrics)
        
        # Determine if rollback is needed
        rollback_needed = self._should_rollback(new_metrics, side_effects)
        
        # Create validation result
        result = ValidationResult(
            action_id=f"{action.action_type.value}_{service}_{int(time.time())}",
            success=improvement > 0 and not rollback_needed,
            metrics_before=current_metrics,
            metrics_after=new_metrics,
            improvement_percentage=improvement,
            time_to_effect=self.simulator.action_effects.get(
                action.action_type, {}
            ).get('time_to_effect', 30),
            side_effects=side_effects,
            rollback_needed=rollback_needed
        )
        
        # Store in history
        self.validation_history.append(result)
        
        # Update service state
        self.simulator.update_service_state(service, new_metrics)
        
        return result
    
    def _calculate_improvement(self, before: Dict[str, float], after: Dict[str, float]) -> float:
        """Calculate overall improvement percentage"""
        improvements = []
        
        # CPU improvement (lower is better)
        if 'cpu_usage' in before and 'cpu_usage' in after:
            cpu_improvement = (before['cpu_usage'] - after['cpu_usage']) / before['cpu_usage']
            improvements.append(cpu_improvement)
        
        # Memory improvement (lower is better)
        if 'memory_usage' in before and 'memory_usage' in after:
            mem_improvement = (before['memory_usage'] - after['memory_usage']) / before['memory_usage']
            improvements.append(mem_improvement)
        
        # Error rate improvement (lower is better)
        if 'error_rate' in before and 'error_rate' in after:
            if before['error_rate'] > 0:
                error_improvement = (before['error_rate'] - after['error_rate']) / before['error_rate']
                improvements.append(error_improvement)
        
        # Latency improvement (lower is better)
        if 'request_latency_ms' in before and 'request_latency_ms' in after:
            latency_improvement = (before['request_latency_ms'] - after['request_latency_ms']) / before['request_latency_ms']
            improvements.append(latency_improvement * 0.5)  # Weight latency less
        
        return sum(improvements) / len(improvements) * 100 if improvements else 0
    
    def _should_rollback(self, metrics: Dict[str, float], side_effects: List[str]) -> bool:
        """Determine if action should be rolled back"""
        
        # Check for critical metrics
        if metrics.get('error_rate', 0) > 0.1:  # >10% error rate
            return True
        if metrics.get('cpu_usage', 0) > 95:  # >95% CPU
            return True
        if metrics.get('memory_usage', 0) > 95:  # >95% memory
            return True
        
        # Check for critical side effects
        critical_effects = {'data_loss', 'security_breach', 'complete_outage'}
        if any(effect in critical_effects for effect in side_effects):
            return True
        
        return False

class LogGenerator:
    """Generates new logs based on simulated metrics"""
    
    def __init__(self):
        self.sequence_num = 0
        
    def generate_fixed_logs(self, 
                           service: str,
                           metrics: Dict[str, float],
                           count: int = 10,
                           interval_seconds: int = 60) -> List[Dict[str, Any]]:
        """Generate logs showing fixed metrics"""
        
        logs = []
        base_time = datetime.utcnow()
        
        for i in range(count):
            timestamp = base_time + timedelta(seconds=i * interval_seconds)
            
            # Add some natural variance
            varied_metrics = {}
            for key, value in metrics.items():
                if isinstance(value, (int, float)):
                    # Add ±5% variance
                    variance = random.uniform(0.95, 1.05)
                    varied_metrics[key] = value * variance
                else:
                    varied_metrics[key] = value
            
            log = {
                'timestamp': timestamp.isoformat(),
                'service': service,
                'level': self._determine_level(varied_metrics),
                'request_id': f'req_{self.sequence_num:08x}',
                'host': f'{service}-1.prod.internal',
                'environment': 'production',
                'metrics': varied_metrics,
                'anomaly': False,  # Fixed = no anomaly
                'message': 'Service recovered after mitigation',
                'mitigation_applied': True
            }
            
            logs.append(log)
            self.sequence_num += 1
        
        return logs
    
    def _determine_level(self, metrics: Dict[str, float]) -> str:
        """Determine log level based on metrics"""
        if metrics.get('error_rate', 0) > 0.05:
            return 'ERROR'
        elif metrics.get('cpu_usage', 0) > 80 or metrics.get('memory_usage', 0) > 80:
            return 'WARNING'
        else:
            return 'INFO'

class MitigationSimulator:
    """Complete mitigation simulation system"""
    
    def __init__(self):
        self.validator = ActionValidator()
        self.log_generator = LogGenerator()
        self.active_mitigations = {}
        
    def simulate_mitigation(self, 
                           anomalous_log: Dict[str, Any],
                           action: MitigationAction,
                           generate_logs: bool = True) -> Dict[str, Any]:
        """Simulate complete mitigation process"""
        
        logger.info(f"Simulating {action.action_type.value} for {action.service}")
        
        # Validate the action
        validation_result = self.validator.validate_action(action, anomalous_log)
        
        # Generate result package
        result = {
            'action': action.__dict__,
            'validation': validation_result.__dict__,
            'success': validation_result.success,
            'logs_generated': []
        }
        
        if validation_result.success and generate_logs:
            # Generate logs showing improvement
            fixed_logs = self.log_generator.generate_fixed_logs(
                service=action.service,
                metrics=validation_result.metrics_after,
                count=10,
                interval_seconds=30
            )
            result['logs_generated'] = fixed_logs
            
            logger.info(f"✅ Mitigation successful! Improvement: {validation_result.improvement_percentage:.1f}%")
        else:
            logger.warning(f"❌ Mitigation failed or needs rollback")
        
        # Store active mitigation
        self.active_mitigations[action.service] = result
        
        return result
    
    def get_mitigation_report(self, service: str) -> Dict[str, Any]:
        """Get detailed report of mitigation for a service"""
        
        if service not in self.active_mitigations:
            return {'error': f'No mitigation found for {service}'}
        
        mitigation = self.active_mitigations[service]
        validation = mitigation['validation']
        
        report = {
            'service': service,
            'action_taken': mitigation['action']['action_type'],
            'success': mitigation['success'],
            'metrics_improvement': {
                'cpu_reduction': validation['metrics_before'].get('cpu_usage', 0) - 
                                validation['metrics_after'].get('cpu_usage', 0),
                'memory_reduction': validation['metrics_before'].get('memory_usage', 0) - 
                                   validation['metrics_after'].get('memory_usage', 0),
                'error_rate_reduction': validation['metrics_before'].get('error_rate', 0) - 
                                       validation['metrics_after'].get('error_rate', 0),
                'overall_improvement': validation['improvement_percentage']
            },
            'time_to_effect_seconds': validation['time_to_effect'],
            'side_effects': validation['side_effects'],
            'new_logs_generated': len(mitigation['logs_generated']),
            'service_health': 'HEALTHY' if mitigation['success'] else 'DEGRADED'
        }
        
        return report

# Example RAG Mitigation Strategies
class RAGMitigationStrategies:
    """Pre-defined mitigation strategies for common issues"""
    
    strategies = {
        'high_cpu': {
            'conditions': lambda m: m.get('cpu_usage', 0) > 85,
            'action': ActionType.RESTART_SERVICE,
            'parameters': {'graceful': True, 'drain_time': 30},
            'confidence': 0.85
        },
        'high_memory': {
            'conditions': lambda m: m.get('memory_usage', 0) > 85,
            'action': ActionType.CLEAR_CACHE,
            'parameters': {'cache_type': 'all'},
            'confidence': 0.75
        },
        'high_error_rate': {
            'conditions': lambda m: m.get('error_rate', 0) > 0.05,
            'action': ActionType.CIRCUIT_BREAKER,
            'parameters': {'threshold': 0.5, 'timeout': 60},
            'confidence': 0.80
        },
        'connection_exhaustion': {
            'conditions': lambda m: m.get('active_connections', 0) > 450,
            'action': ActionType.INCREASE_CONNECTION_POOL,
            'parameters': {'increase_by': 100},
            'confidence': 0.90
        },
        'high_latency': {
            'conditions': lambda m: m.get('request_latency_ms', 0) > 500,
            'action': ActionType.SCALE_HORIZONTAL,
            'parameters': {'instances': 2},
            'confidence': 0.70
        }
    }
    
    @classmethod
    def get_mitigation(cls, metrics: Dict[str, float], service: str) -> Optional[MitigationAction]:
        """Get appropriate mitigation based on metrics"""
        
        for issue_type, strategy in cls.strategies.items():
            if strategy['conditions'](metrics):
                return MitigationAction(
                    action_type=strategy['action'],
                    service=service,
                    parameters=strategy['parameters'],
                    confidence=strategy['confidence'],
                    source='rag',
                    timestamp=datetime.utcnow().isoformat(),
                    expected_impact={
                        'issue_type': issue_type,
                        'expected_resolution_time': 60
                    }
                )
        return None

# Integration Example
def process_anomalous_log(log: Dict[str, Any]) -> Dict[str, Any]:
    """Complete processing pipeline for an anomalous log"""
    
    logger.info(f"Processing anomaly for service: {log.get('service')}")
    
    # Get mitigation from RAG
    mitigation = RAGMitigationStrategies.get_mitigation(
        log.get('metrics', {}),
        log.get('service', 'unknown')
    )
    
    if not mitigation:
        logger.warning("No mitigation strategy found, escalating to LLM agent")
        return {'status': 'escalated', 'reason': 'no_matching_strategy'}
    
    # Simulate the mitigation
    simulator = MitigationSimulator()
    result = simulator.simulate_mitigation(log, mitigation, generate_logs=True)
    
    # Get detailed report
    report = simulator.get_mitigation_report(log.get('service'))
    
    return {
        'status': 'mitigated' if result['success'] else 'failed',
        'mitigation': mitigation.__dict__,
        'result': result,
        'report': report
    }

# Example usage
if __name__ == "__main__":
    # Sample anomalous log
    anomalous_log = {
        'timestamp': '2025-08-14T10:00:00',
        'service': 'api-gateway',
        'level': 'ERROR',
        'metrics': {
            'cpu_usage': 92.5,
            'memory_usage': 78.3,
            'error_rate': 0.08,
            'request_latency_ms': 450,
            'active_connections': 380
        },
        'anomaly': True,
        'message': 'High CPU usage detected'
    }
    
    # Process the anomaly
    result = process_anomalous_log(anomalous_log)
    
    # Print results
    print(json.dumps(result, indent=2))
