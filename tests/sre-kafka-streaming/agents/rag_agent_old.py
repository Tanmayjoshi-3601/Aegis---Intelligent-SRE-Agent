"""
RAG Agent (Retrieval-Augmented Generation)
=========================================
Agent that handles common errors using retrieval-augmented generation
with a knowledge base of common mitigation strategies and playbooks.
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
        self.openai_api_key = os.getenv('OPENAI_API_KEY', '')
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
        """Create default mitigation playbooks"""
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
                        "action_type": "kill_processes",
                        "description": "Kill memory-intensive processes",
                        "commands": ["pkill -f memory-intensive-process", "kill -9 $(pgrep java)"],
                        "expected_duration": 15,
                        "risk_level": "high",
                        "prerequisites": ["Identify safe processes to kill"],
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
        logger.info("Created 5 default playbooks")
    
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
            
            # Classify the error type
            error_type = self._classify_error(log_entry, anomaly_decision)
            
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
                    'reasoning': f"RAG agent processed {error_type} using {len(selected_actions)} actions"
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
                    'needs_escalation': True
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
                'needs_escalation': True
            }
    
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
        
        # Check for critical errors
        if level in ['CRITICAL', 'ERROR']:
            return 'critical_error'
        
        # Default fallback
        return 'unknown_error'
    
    def _retrieve_playbook(self, error_type: str) -> Optional[Dict]:
        """Retrieve the appropriate playbook for the error type"""
        return self.mitigation_playbooks.get(error_type)
    
    def _generate_context(self, log_entry, anomaly_decision, playbook) -> str:
        """Generate context for LLM analysis"""
        return f"""
Error Type: {playbook['description']}
Log Level: {log_entry.level}
Service: {log_entry.service}
Message: {log_entry.message}
Metrics: {log_entry.metrics}
Anomaly Decision: {anomaly_decision}
Available Actions: {[action.description for action in playbook['actions']]}
"""
    
    async def _get_llm_recommendations(self, context: str) -> Dict:
        """Get LLM recommendations for the error"""
        if not self.openai_api_key:
            return {'recommendation': 'No API key available', 'confidence': 0.0}
        
        try:
            headers = {
                "Authorization": f"Bearer {self.openai_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are an SRE expert. Analyze the error and recommend the best mitigation actions."},
                    {"role": "user", "content": context}
                ],
                "max_tokens": self.max_tokens,
                "temperature": 0.1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.openai_base_url}/chat/completions", headers=headers, json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        return {'recommendation': content, 'confidence': 0.8}
                    else:
                        return {'recommendation': 'API call failed', 'confidence': 0.0}
        except Exception as e:
            logger.error(f"LLM API error: {e}")
            return {'recommendation': f'Error: {str(e)}', 'confidence': 0.0}
    
    def _select_actions(self, playbook: Dict, llm_recommendations: Dict) -> List[MitigationAction]:
        """Select appropriate actions based on LLM recommendations"""
        # For now, return all actions from the playbook
        # In a real implementation, this would parse LLM recommendations
        return playbook['actions']
    
    async def _execute_actions(self, actions: List[MitigationAction]) -> List[Dict]:
        """Execute mitigation actions"""
        results = []
        for action in actions:
            result = {
                'action': action.description,
                'status': 'simulated',
                'duration': action.expected_duration,
                'risk_level': action.risk_level
            }
            results.append(result)
            logger.info(f"Simulated execution: {action.description}")
        return results
    
    def _needs_escalation(self, execution_results: List[Dict], llm_recommendations: Dict) -> bool:
        """Determine if escalation is needed"""
        # Check if any actions failed or if confidence is low
        failed_actions = [r for r in execution_results if r.get('status') == 'failed']
        low_confidence = llm_recommendations.get('confidence', 0) < 0.5
        
        return len(failed_actions) > 0 or low_confidence
