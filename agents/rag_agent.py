"""
RAG Agent (Retrieval-Augmented Generation) - Updated Version
==========================================================
Agent that handles common errors using retrieval-augmented generation
with a knowledge base of common mitigation strategies and playbooks.
Excludes service_crash (goes to Advanced LLM).
"""

import json
import logging
import asyncio
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import sqlite3
import re
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ActionType(Enum):
    """Types of actions the RAG agent can take"""
    RESTART_SERVICE = "restart_service"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    CLEAR_CACHE = "clear_cache"
    KILL_PROCESSES = "kill_processes"
    UPDATE_CONFIG = "update_config"
    ROLLBACK = "rollback"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class MitigationAction:
    """Represents a mitigation action"""
    action_type: ActionType
    description: str
    commands: List[str]
    expected_duration: int  # seconds
    risk_level: str  # low, medium, high
    prerequisites: List[str]
    rollback_commands: List[str]

class RAGAgent:
    """
    RAG Agent for handling common errors with retrieval-augmented generation
    """
    
    def __init__(self, knowledge_base_path: str = "data/knowledge_base", max_context_length: int = 4000):
        """
        Initialize the RAG Agent
        
        Args:
            knowledge_base_path: Path to knowledge base directory
            max_context_length: Maximum context length for LLM
        """
        self.knowledge_base_path = Path(knowledge_base_path)
        self.max_context_length = max_context_length
        self.mitigation_playbooks = {}
        self.service_playbooks = {}
        self.stats = {
            'total_processed': 0,
            'actions_executed': 0,
            'successful_resolutions': 0,
            'failed_resolutions': 0
        }
        
        # OpenAI API Configuration
        self.openai_api_key = "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"
        self.openai_base_url = "https://api.openai.com/v1"
        self.model = "gpt-4"
        self.max_tokens = 1000
        
        # Initialize knowledge base
        self._initialize_knowledge_base()
        
        logger.info(f"✅ RAG Agent initialized with knowledge base at {knowledge_base_path}")
    
    def _initialize_knowledge_base(self):
        """Initialize the knowledge base with mitigation playbooks"""
        try:
            # Create knowledge base directory if it doesn't exist
            self.knowledge_base_path.mkdir(parents=True, exist_ok=True)
            
            # Load or create default playbooks
            self._load_playbooks()
            
            logger.info("Knowledge base initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing knowledge base: {e}")
            self._create_default_playbooks()
    
    def _load_playbooks(self):
        """Load mitigation playbooks from knowledge base"""
        playbooks_file = self.knowledge_base_path / "mitigation_playbooks.json"
        
        if playbooks_file.exists():
            try:
                with open(playbooks_file, 'r') as f:
                    playbooks_data = json.load(f)
                
                # Convert playbooks data to MitigationAction objects
                for error_type, playbook in playbooks_data.items():
                    actions = []
                    for action_data in playbook.get('actions', []):
                        action = MitigationAction(
                            action_type=ActionType(action_data['action_type']),
                            description=action_data['description'],
                            commands=action_data['commands'],
                            expected_duration=action_data['expected_duration'],
                            risk_level=action_data['risk_level'],
                            prerequisites=action_data.get('prerequisites', []),
                            rollback_commands=action_data.get('rollback_commands', [])
                        )
                        actions.append(action)
                    
                    self.mitigation_playbooks[error_type] = {
                        'description': playbook['description'],
                        'actions': actions,
                        'success_rate': playbook.get('success_rate', 0.8)
                    }
                
                logger.info(f"Loaded {len(self.mitigation_playbooks)} playbooks from knowledge base")
                
            except Exception as e:
                logger.error(f"Error loading playbooks: {e}")
                self._create_default_playbooks()
        else:
            self._create_default_playbooks()
    
    def _create_default_playbooks(self):
        """Create default mitigation playbooks (EXCLUDES service_crash)"""
        default_playbooks = {
            "cpu_overload": {
                "description": "High CPU usage across services",
                "actions": [
                    {
                        "action_type": "scale_up",
                        "description": "Scale up service instances",
                        "commands": ["kubectl scale deployment --replicas=5", "docker-compose up --scale web=5"],
                        "expected_duration": 120,
                        "risk_level": "low",
                        "prerequisites": ["Check available resources"],
                        "rollback_commands": ["kubectl scale deployment --replicas=3"]
                    },
                    {
                        "action_type": "clear_cache",
                        "description": "Clear application cache",
                        "commands": ["redis-cli flushall", "systemctl restart memcached"],
                        "expected_duration": 30,
                        "risk_level": "low",
                        "prerequisites": ["Backup cache data"],
                        "rollback_commands": ["redis-cli restore backup"]
                    }
                ],
                "success_rate": 0.85
            },
            "memory_leak": {
                "description": "Memory usage spike and garbage collection issues",
                "actions": [
                    {
                        "action_type": "restart_service",
                        "description": "Restart affected service",
                        "commands": ["systemctl restart web-service", "docker restart web-container"],
                        "expected_duration": 60,
                        "risk_level": "medium",
                        "prerequisites": ["Check service dependencies"],
                        "rollback_commands": ["systemctl start web-service"]
                    },
                    {
                        "action_type": "clear_cache",
                        "description": "Clear memory cache",
                        "commands": ["echo 3 > /proc/sys/vm/drop_caches", "systemctl restart memcached"],
                        "expected_duration": 15,
                        "risk_level": "low",
                        "prerequisites": ["Check memory usage"],
                        "rollback_commands": ["systemctl restart affected-services"]
                    }
                ],
                "success_rate": 0.75
            },
            "database_slowdown": {
                "description": "Slow database queries and connection pool exhaustion",
                "actions": [
                    {
                        "action_type": "update_config",
                        "description": "Optimize database configuration",
                        "commands": ["mysql -e 'SET GLOBAL max_connections=200'", "postgresql.conf optimization"],
                        "expected_duration": 45,
                        "risk_level": "medium",
                        "prerequisites": ["Backup database"],
                        "rollback_commands": ["mysql -e 'SET GLOBAL max_connections=100'"]
                    },
                    {
                        "action_type": "clear_cache",
                        "description": "Clear database query cache",
                        "commands": ["mysql -e 'FLUSH QUERY CACHE'", "redis-cli flushdb"],
                        "expected_duration": 20,
                        "risk_level": "low",
                        "prerequisites": ["Check cache hit rates"],
                        "rollback_commands": ["Restore from backup"]
                    }
                ],
                "success_rate": 0.80
            },
            "network_latency": {
                "description": "High network latency and timeout errors",
                "actions": [
                    {
                        "action_type": "update_config",
                        "description": "Increase timeout values",
                        "commands": ["Update nginx timeout settings", "Increase application timeouts"],
                        "expected_duration": 30,
                        "risk_level": "low",
                        "prerequisites": ["Check current timeout values"],
                        "rollback_commands": ["Restore original timeout settings"]
                    },
                    {
                        "action_type": "scale_up",
                        "description": "Add load balancer instances",
                        "commands": ["kubectl scale deployment lb --replicas=3", "Add CDN endpoints"],
                        "expected_duration": 90,
                        "risk_level": "medium",
                        "prerequisites": ["Check network capacity"],
                        "rollback_commands": ["kubectl scale deployment lb --replicas=1"]
                    }
                ],
                "success_rate": 0.70
            }
        }
        
        # Convert to MitigationAction objects
        for error_type, playbook in default_playbooks.items():
            actions = []
            for action_data in playbook['actions']:
                action = MitigationAction(
                    action_type=ActionType(action_data['action_type']),
                    description=action_data['description'],
                    commands=action_data['commands'],
                    expected_duration=action_data['expected_duration'],
                    risk_level=action_data['risk_level'],
                    prerequisites=action_data.get('prerequisites', []),
                    rollback_commands=action_data.get('rollback_commands', [])
                )
                actions.append(action)
            
            self.mitigation_playbooks[error_type] = {
                'description': playbook['description'],
                'actions': actions,
                'success_rate': playbook['success_rate']
            }
        
        # Save to file
        self._save_playbooks()
        logger.info("Created 4 default playbooks (excludes service_crash)")
    
    def _save_playbooks(self):
        """Save playbooks to knowledge base"""
        try:
            playbooks_data = {}
            for error_type, playbook in self.mitigation_playbooks.items():
                actions_data = []
                for action in playbook['actions']:
                    actions_data.append({
                        'action_type': action.action_type.value,
                        'description': action.description,
                        'commands': action.commands,
                        'expected_duration': action.expected_duration,
                        'risk_level': action.risk_level,
                        'prerequisites': action.prerequisites,
                        'rollback_commands': action.rollback_commands
                    })
                
                playbooks_data[error_type] = {
                    'description': playbook['description'],
                    'actions': actions_data,
                    'success_rate': playbook['success_rate']
                }
            
            playbooks_file = self.knowledge_base_path / "mitigation_playbooks.json"
            with open(playbooks_file, 'w') as f:
                json.dump(playbooks_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving playbooks: {e}")
    
    async def process(self, log_entry, anomaly_decision) -> Dict[str, Any]:
        """
        Process an error using RAG-based mitigation
        
        Args:
            log_entry: LogEntry object
            anomaly_decision: Decision from anomaly detection agent
            
        Returns:
            Processing result with mitigation actions and recommendations
        """
        try:
            self.stats['total_processed'] += 1
            
            # Detailed thought process
            thought_process = self._analyze_anomaly(log_entry, anomaly_decision)
            
            # Classify the error type
            error_type = self._classify_error(log_entry, anomaly_decision)
            
            # Check if this should go to Advanced LLM (service crash)
            if error_type == 'service_crash':
                return {
                    'decision': 'escalate',
                    'error_type': 'service_crash',
                    'reasoning': 'Service crash detected - escalating to Advanced LLM for complex analysis',
                    'confidence': 0.9,
                    'needs_escalation': True,
                    'thought_process': thought_process
                }
            
            # Retrieve relevant playbooks
            playbook = self._retrieve_playbook(error_type)
            
            if playbook:
                # Generate context for LLM
                context = self._generate_context(log_entry, anomaly_decision, playbook)
                
                # Get LLM recommendations
                llm_recommendations = await self._get_llm_recommendations(context)
                
                # Select and execute mitigation actions
                selected_actions = self._select_actions(playbook, llm_recommendations)
                
                # Execute actions
                execution_results = await self._execute_actions(selected_actions)
                
                # Determine if escalation is needed
                needs_escalation = self._needs_escalation(execution_results, llm_recommendations)
                
                result = {
                    'decision': 'mitigated' if not needs_escalation else 'escalate',
                    'error_type': error_type,
                    'playbook_used': playbook['description'],
                    'actions_executed': selected_actions,
                    'execution_results': execution_results,
                    'llm_recommendations': llm_recommendations,
                    'needs_escalation': needs_escalation,
                    'confidence': 0.85,
                    'reasoning': f"RAG agent processed {error_type} using {len(selected_actions)} actions",
                    'thought_process': thought_process
                }
                
                if not needs_escalation:
                    self.stats['successful_resolutions'] += 1
                else:
                    self.stats['failed_resolutions'] += 1
                
            else:
                # No playbook found, escalate to advanced LLM
                result = {
                    'decision': 'escalate',
                    'error_type': 'unknown',
                    'reasoning': 'No suitable playbook found for this error type',
                    'confidence': 0.5,
                    'needs_escalation': True,
                    'thought_process': thought_process
                }
                self.stats['failed_resolutions'] += 1
            
            logger.info(f"RAG Agent processed {log_entry.request_id}: {result['decision']}")
            return result
            
        except Exception as e:
            logger.error(f"Error in RAG agent processing: {e}")
            return {
                'decision': 'escalate',
                'error_type': 'error',
                'reasoning': f"RAG agent error: {str(e)}",
                'confidence': 0.0,
                'needs_escalation': True,
                'thought_process': {'error': str(e)}
            }
    
    def _analyze_anomaly(self, log_entry, anomaly_decision) -> Dict[str, Any]:
        """Detailed analysis and thought process"""
        metrics = log_entry.metrics
        level = log_entry.level
        
        analysis = {
            'timestamp': datetime.now().isoformat(),
            'service': log_entry.service,
            'anomaly_confidence': anomaly_decision.get('confidence', 0.0),
            'metrics_analysis': {},
            'risk_assessment': 'low',
            'recommended_approach': 'standard_mitigation'
        }
        
        # Analyze each metric
        if metrics.get('cpu_usage', 0) > 90:
            analysis['metrics_analysis']['cpu'] = {
                'value': metrics['cpu_usage'],
                'status': 'critical',
                'impact': 'Service performance degradation'
            }
            analysis['risk_assessment'] = 'high'
        elif metrics.get('cpu_usage', 0) > 80:
            analysis['metrics_analysis']['cpu'] = {
                'value': metrics['cpu_usage'],
                'status': 'warning',
                'impact': 'Potential performance issues'
            }
            analysis['risk_assessment'] = 'medium'
        
        if metrics.get('memory_usage', 0) > 85:
            analysis['metrics_analysis']['memory'] = {
                'value': metrics['memory_usage'],
                'status': 'critical',
                'impact': 'Memory exhaustion risk'
            }
            analysis['risk_assessment'] = 'high'
        
        if metrics.get('error_rate', 0) > 0.1:
            analysis['metrics_analysis']['error_rate'] = {
                'value': metrics['error_rate'],
                'status': 'critical',
                'impact': 'Service reliability compromised'
            }
            analysis['risk_assessment'] = 'high'
        
        if metrics.get('request_latency_ms', 0) > 5000:
            analysis['metrics_analysis']['latency'] = {
                'value': metrics['request_latency_ms'],
                'status': 'critical',
                'impact': 'User experience degraded'
            }
        
        # Determine approach
        if level in ['CRITICAL'] and analysis['risk_assessment'] == 'high':
            analysis['recommended_approach'] = 'immediate_escalation'
        elif analysis['risk_assessment'] == 'high':
            analysis['recommended_approach'] = 'aggressive_mitigation'
        else:
            analysis['recommended_approach'] = 'standard_mitigation'
        
        return analysis
    
    def _classify_error(self, log_entry, anomaly_decision) -> str:
        """Classify the error type based on log entry and anomaly decision"""
        metrics = log_entry.metrics
        level = log_entry.level
        
        # Check for CPU overload
        if metrics.get('cpu_usage', 0) > 90:
            return 'cpu_overload'
        
        # Check for memory issues
        if metrics.get('memory_usage', 0) > 85:
            return 'memory_leak'
        
        # Check for database issues
        if metrics.get('request_latency_ms', 0) > 5000:
            return 'database_slowdown'
        
        # Check for network issues
        if metrics.get('error_rate', 0) > 0.1:
            return 'network_latency'
        
        # Check for critical errors (service crash)
        if level in ['CRITICAL'] and metrics.get('error_rate', 0) > 0.2:
            return 'service_crash'
        
        # Default classification
        return 'unknown'
    
    def _retrieve_playbook(self, error_type: str) -> Optional[Dict[str, Any]]:
        """Retrieve relevant playbook for error type"""
        return self.mitigation_playbooks.get(error_type)
    
    def _generate_context(self, log_entry, anomaly_decision, playbook) -> str:
        """Generate context for LLM processing"""
        context = f"""
Error Context:
- Service: {log_entry.service}
- Log Level: {log_entry.level}
- Timestamp: {log_entry.timestamp}
- Host: {log_entry.host}
- Environment: {log_entry.environment}

Metrics:
- CPU Usage: {log_entry.metrics.get('cpu_usage', 'N/A')}%
- Memory Usage: {log_entry.metrics.get('memory_usage', 'N/A')}%
- Response Time: {log_entry.metrics.get('request_latency_ms', 'N/A')}ms
- Error Rate: {log_entry.metrics.get('error_rate', 'N/A')}%

Anomaly Detection:
- Decision: {anomaly_decision.get('decision', 'unknown')}
- Confidence: {anomaly_decision.get('confidence', 0.0)}
- Reasoning: {anomaly_decision.get('reasoning', 'No reasoning provided')}

Available Mitigation Actions:
"""
        
        for i, action in enumerate(playbook['actions'], 1):
            context += f"""
{i}. {action.description}
   - Type: {action.action_type.value}
   - Risk Level: {action.risk_level}
   - Expected Duration: {action.expected_duration}s
   - Commands: {', '.join(action.commands)}
   - Prerequisites: {', '.join(action.prerequisites)}
"""
        
        context += f"""
Playbook Success Rate: {playbook['success_rate']}

Please analyze this error and recommend the best mitigation actions to take. Consider the risk level, expected duration, and success rate of each action.
"""
        
        return context
    
    async def _get_llm_recommendations(self, context: str) -> Dict[str, Any]:
        """Get recommendations from OpenAI LLM"""
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": """You are an SRE (Site Reliability Engineering) expert. Analyze the provided error context and recommend the best mitigation actions. Consider risk levels, expected duration, and success rates. Provide specific, actionable recommendations."""
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                "max_tokens": self.max_tokens,
                "temperature": 0.3
            }
            
            response = requests.post(
                f"{self.openai_base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Parse LLM response
                recommendations = self._parse_llm_response(content)
                
                logger.info(f"LLM recommendations received: {len(recommendations.get('recommended_actions', []))} actions")
                return recommendations
            else:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return {
                    'recommended_actions': [],
                    'reasoning': 'LLM API call failed',
                    'confidence': 0.0
                }
                
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return {
                'recommended_actions': [],
                'reasoning': f'LLM API error: {str(e)}',
                'confidence': 0.0
            }
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM response to extract recommendations"""
        try:
            # Simple parsing - extract action numbers and reasoning
            lines = content.split('\n')
            recommended_actions = []
            reasoning = ""
            
            for line in lines:
                line = line.strip()
                if line.startswith(('1.', '2.', '3.', '4.', '5.')):
                    # Extract action number
                    action_match = re.search(r'(\d+)\.', line)
                    if action_match:
                        action_num = int(action_match.group(1))
                        recommended_actions.append(action_num)
                elif line and not line.startswith('-') and not line.startswith('*'):
                    reasoning += line + " "
            
            return {
                'recommended_actions': recommended_actions,
                'reasoning': reasoning.strip(),
                'confidence': 0.8 if recommended_actions else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return {
                'recommended_actions': [],
                'reasoning': 'Failed to parse LLM response',
                'confidence': 0.0
            }
    
    def _select_actions(self, playbook: Dict[str, Any], llm_recommendations: Dict[str, Any]) -> List[MitigationAction]:
        """Select mitigation actions based on LLM recommendations"""
        actions = playbook['actions']
        recommended_indices = llm_recommendations.get('recommended_actions', [])
        
        selected_actions = []
        
        # If LLM provided recommendations, use them
        if recommended_indices:
            for idx in recommended_indices:
                if 1 <= idx <= len(actions):
                    selected_actions.append(actions[idx - 1])
        
        # If no LLM recommendations or they're invalid, use default strategy
        if not selected_actions:
            # Select actions based on risk level (prefer low risk first)
            low_risk_actions = [a for a in actions if a.risk_level == 'low']
            medium_risk_actions = [a for a in actions if a.risk_level == 'medium']
            high_risk_actions = [a for a in actions if a.risk_level == 'high']
            
            selected_actions = low_risk_actions[:1] + medium_risk_actions[:1] + high_risk_actions[:1]
        
        return selected_actions[:3]  # Limit to 3 actions
    
    async def _execute_actions(self, actions: List[MitigationAction]) -> List[Dict[str, Any]]:
        """Execute mitigation actions (simulated)"""
        results = []
        
        for action in actions:
            try:
                # Simulate action execution
                await asyncio.sleep(1)  # Simulate execution time
                
                # Simulate success/failure based on risk level
                success_rate = 0.9 if action.risk_level == 'low' else 0.7 if action.risk_level == 'medium' else 0.5
                success = asyncio.get_event_loop().time() % 1 < success_rate
                
                result = {
                    'action': action.description,
                    'type': action.action_type.value,
                    'risk_level': action.risk_level,
                    'duration': action.expected_duration,
                    'success': success,
                    'commands_executed': action.commands,
                    'timestamp': datetime.now().isoformat()
                }
                
                if success:
                    self.stats['actions_executed'] += 1
                    logger.info(f"Action executed successfully: {action.description}")
                else:
                    logger.warning(f"Action failed: {action.description}")
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error executing action {action.description}: {e}")
                results.append({
                    'action': action.description,
                    'type': action.action_type.value,
                    'risk_level': action.risk_level,
                    'duration': action.expected_duration,
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def _needs_escalation(self, execution_results: List[Dict[str, Any]], llm_recommendations: Dict[str, Any]) -> bool:
        """Determine if escalation to advanced LLM is needed"""
        # Check if any actions failed
        failed_actions = [r for r in execution_results if not r.get('success', True)]
        
        # Check if LLM confidence is low
        low_confidence = llm_recommendations.get('confidence', 0.0) < 0.6
        
        # Check if all actions are high risk
        all_high_risk = all(r.get('risk_level') == 'high' for r in execution_results)
        
        # Escalate if any of these conditions are met
        needs_escalation = (
            len(failed_actions) > 0 or
            low_confidence or
            all_high_risk or
            len(execution_results) == 0
        )
        
        if needs_escalation:
            logger.info(f"Escalation needed: {len(failed_actions)} failed actions, confidence: {llm_recommendations.get('confidence', 0.0)}")
        
        return needs_escalation
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            **self.stats,
            'resolution_rate': self.stats['successful_resolutions'] / max(self.stats['total_processed'], 1),
            'playbook_count': len(self.mitigation_playbooks)
        }
