"""
SRE Agent Orchestrator
======================
Main orchestration layer for the Intelligent SRE Agent system.

This orchestrator coordinates:
1. Anomaly Detection Agent
2. RAG Agent (for common errors)
3. Mitigation Agent (for action execution and validation)
4. Advanced LLM Agent (for uncommon errors)
5. Database Storage
6. Paging System
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path

# Import our agents
from agents.anomaly_detector_agent import AnomalyDetectorAgent
from agents.rag_agent import RAGAgent
from agents.mitigation_agent import MitigationAgent
from agents.advanced_llm_agent import AdvancedLLMAgent
from agents.paging_agent import PagingAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LogSeverity(Enum):
    """Log severity levels"""
    NORMAL = "normal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class LogEntry:
    """Standardized log entry structure"""
    timestamp: str
    service: str
    level: str
    request_id: str
    host: str
    environment: str
    metrics: Dict[str, Any]
    anomaly: bool
    message: Optional[str] = None
    severity: LogSeverity = LogSeverity.NORMAL
    analysis: Optional[Dict[str, Any]] = None

@dataclass
class AgentDecision:
    """Decision made by an agent"""
    agent_name: str
    decision: str
    confidence: float
    reasoning: str
    timestamp: str
    metadata: Dict[str, Any]

class SREAgentOrchestrator:
    """
    Main orchestrator for the SRE Agent system
    """
    
    def __init__(self, config_path: str = "config/sre_agent_config.json"):
        """
        Initialize the SRE Agent Orchestrator
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.agents = {}
        self.stats = {
            'total_logs_processed': 0,
            'anomalies_detected': 0,
            'common_errors': 0,
            'uncommon_errors': 0,
            'pages_sent': 0,
            'database_stores': 0
        }
        
        # Initialize all agents
        self._initialize_agents()
        
        # Initialize database for storing logs and analysis history
        self._init_database()
        
        logger.info("✅ SRE Agent Orchestrator initialized successfully")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Config file {config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "agents": {
                "anomaly_detector": {
                    "enabled": True,
                    "model_path": "ml_pipeline/saved_models",
                    "confidence_threshold": 0.7
                },
                "rag": {
                    "enabled": True,
                    "knowledge_base_path": "data/knowledge_base",
                    "max_context_length": 4000
                },
                "mitigation": {
                    "enabled": True
                },
                "advanced_llm": {
                    "enabled": True,
                    "model": "gpt-4",
                    "max_tokens": 2000
                },
                "paging": {
                    "enabled": True,
                    "paging_webhook": "https://api.pagerduty.com/v2/incidents",
                    "escalation_policy": "default"
                }
            },
            "processing": {
                "batch_size": 100,
                "max_retries": 3,
                "timeout_seconds": 30
            }
        }
    
    def _initialize_agents(self):
        """Initialize all agents"""
        try:
            # Initialize Anomaly Detection Agent
            if self.config["agents"]["anomaly_detector"]["enabled"]:
                self.agents["anomaly_detector"] = AnomalyDetectorAgent(
                    model_path=self.config["agents"]["anomaly_detector"]["model_path"],
                    confidence_threshold=self.config["agents"]["anomaly_detector"]["confidence_threshold"]
                )
            
            # Initialize RAG Agent
            if self.config["agents"]["rag"]["enabled"]:
                self.agents["rag"] = RAGAgent(
                    knowledge_base_path=self.config["agents"]["rag"]["knowledge_base_path"],
                    max_context_length=self.config["agents"]["rag"]["max_context_length"]
                )
            
            # Initialize Mitigation Agent
            if self.config["agents"]["mitigation"]["enabled"]:
                self.agents["mitigation"] = MitigationAgent()
            
            # Initialize Advanced LLM Agent
            if self.config["agents"]["advanced_llm"]["enabled"]:
                self.agents["advanced_llm"] = AdvancedLLMAgent(
                    model=self.config["agents"]["advanced_llm"]["model"],
                    max_tokens=self.config["agents"]["advanced_llm"]["max_tokens"]
                )
            
            # Initialize Paging Agent
            if self.config["agents"]["paging"]["enabled"]:
                self.agents["paging"] = PagingAgent(
                    webhook_url=self.config["agents"]["paging"]["paging_webhook"],
                    escalation_policy=self.config["agents"]["paging"]["escalation_policy"]
                )
            
            logger.info(f"✅ Initialized {len(self.agents)} agents")
        
        except Exception as e:
            logger.error(f"❌ Error initializing agents: {e}")
            raise

    def _init_database(self):
        """Initialize database for storing logs and analysis history"""
        try:
            db_path = Path("data/sre_agent.db")
            db_path.parent.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create logs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT UNIQUE,
                    timestamp TEXT,
                    service TEXT,
                    level TEXT,
                    host TEXT,
                    environment TEXT,
                    metrics TEXT,
                    anomaly BOOLEAN,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create analysis history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT,
                    agent_name TEXT,
                    decision TEXT,
                    confidence REAL,
                    reasoning TEXT,
                    metadata TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create mitigation actions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS mitigation_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT,
                    action_type TEXT,
                    description TEXT,
                    success BOOLEAN,
                    execution_time REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            logger.info("✅ Database initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Error initializing database: {e}")
            raise
    
    async def process_log(self, log_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single log entry through the entire pipeline
        
        Args:
            log_data: Raw log data from Kafka
            
        Returns:
            Processing result with decisions and actions taken
        """
        try:
            # Convert to standardized log entry
            log_entry = self._standardize_log(log_data)
            self.stats['total_logs_processed'] += 1
            
            result = {
                'log_id': log_entry.request_id,
                'timestamp': log_entry.timestamp,
                'service': log_entry.service,
                'decisions': [],
                'actions_taken': [],
                'processing_time': None
            }
            
            start_time = datetime.now()
            
            # Step 1: Anomaly Detection
            anomaly_decision = await self._run_anomaly_detection(log_entry)
            result['decisions'].append(anomaly_decision)
            
            if anomaly_decision.decision == "anomaly":
                self.stats['anomalies_detected'] += 1
                
                # Step 2: RAG Agent for mitigation (handles both common and uncommon errors)
                rag_result = await self._run_rag_agent(log_entry, anomaly_decision)
                result['actions_taken'].append(rag_result)
                
                # Step 3: Mitigation Agent (if RAG found solution and no escalation)
                if not rag_result.get("needs_escalation", False):
                    mitigation_result = await self._run_mitigation_agent(log_entry, rag_result)
                    result["actions_taken"].append(mitigation_result)
                    self.stats['common_errors'] += 1
                else:
                    self.stats['uncommon_errors'] += 1
                    
                    # Step 4: Advanced LLM Agent for complex errors
                    llm_result = await self._run_advanced_llm_agent(log_entry, anomaly_decision, rag_result)
                    result['actions_taken'].append(llm_result)
                    
                    # Step 5: Page human for complex errors
                    paging_result = await self._page_human(log_entry, llm_result)
                    result['actions_taken'].append(paging_result)
                    self.stats['pages_sent'] += 1
                    
            else:  # No anomaly
                # Store in database
                db_result = await self._store_normal_log(log_entry)
                result['actions_taken'].append(db_result)
                self.stats['database_stores'] += 1
            
            result['processing_time'] = (datetime.now() - start_time).total_seconds()
            
            logger.info(f"Processed log {log_entry.request_id} in {result['processing_time']:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error processing log: {e}")
            return {
                'error': str(e),
                'log_id': log_data.get('request_id', 'unknown'),
                'timestamp': datetime.now().isoformat()
            }
    
    def _standardize_log(self, log_data: Dict[str, Any]) -> LogEntry:
        """Convert raw log data to standardized LogEntry"""
        return LogEntry(
            timestamp=log_data.get('timestamp', datetime.now().isoformat()),
            service=log_data.get('service', 'unknown'),
            level=log_data.get('level', 'INFO'),
            request_id=log_data.get('request_id', 'unknown'),
            host=log_data.get('host', 'unknown'),
            environment=log_data.get('environment', 'production'),
            metrics=log_data.get('metrics', {}),
            anomaly=log_data.get('anomaly', False),
            message=log_data.get('message', '')
        )
    
    async def _run_anomaly_detection(self, log_entry: LogEntry) -> AgentDecision:
        """Run anomaly detection on the log entry"""
        if "anomaly_detector" not in self.agents:
            raise RuntimeError("Anomaly detector agent not initialized")
        
        result = await self.agents["anomaly_detector"].analyze(log_entry)
        
        return AgentDecision(
            agent_name="anomaly_detector",
            decision=result['decision'],
            confidence=result['confidence'],
            reasoning=result['reasoning'],
            timestamp=datetime.now().isoformat(),
            metadata=result.get('metadata', {})
        )
    
    async def _run_rag_agent(self, log_entry: LogEntry, anomaly_decision: AgentDecision) -> Dict[str, Any]:
        """Run RAG agent for error mitigation"""
        if "rag" not in self.agents:
            raise RuntimeError("RAG agent not initialized")
        
        return await self.agents["rag"].process(log_entry, anomaly_decision)
    
    async def _run_mitigation_agent(self, log_entry: LogEntry, rag_result: Dict[str, Any]) -> Dict[str, Any]:
        """Run mitigation agent to execute and validate actions"""
        if "mitigation" not in self.agents:
            raise RuntimeError("Mitigation agent not initialized")
        
        return await self.agents["mitigation"].execute_mitigation(log_entry, rag_result)
    
    async def _run_advanced_llm_agent(self, log_entry: LogEntry, anomaly_decision: AgentDecision, rag_result: Dict[str, Any]) -> Dict[str, Any]:
        """Run advanced LLM agent for complex errors"""
        if "advanced_llm" not in self.agents:
            raise RuntimeError("Advanced LLM agent not initialized")
        
        return await self.agents["advanced_llm"].process(log_entry, anomaly_decision, rag_result)
    
    async def _store_normal_log(self, log_entry: LogEntry) -> Dict[str, Any]:
        """Store normal log in database"""
        try:
            db_path = Path("data/sre_agent.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO logs 
                (request_id, timestamp, service, level, host, environment, metrics, anomaly, message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_entry.request_id,
                log_entry.timestamp,
                log_entry.service,
                log_entry.level,
                log_entry.host,
                log_entry.environment,
                json.dumps(log_entry.metrics),
                log_entry.anomaly,
                log_entry.message
            ))
            
            conn.commit()
            conn.close()
            
            return {
                'action': 'store_log',
                'success': True,
                'log_id': log_entry.request_id,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error storing log: {e}")
            return {
                'action': 'store_log',
                'success': False,
                'error': str(e),
                'log_id': log_entry.request_id
            }
    
    async def _page_human(self, log_entry: LogEntry, llm_result: Dict[str, Any]) -> Dict[str, Any]:
        """Page human for uncommon errors"""
        if "paging" not in self.agents:
            raise RuntimeError("Paging agent not initialized")
        
        return await self.agents["paging"].send_page(log_entry, llm_result)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return {
            **self.stats,
            'agents_initialized': len(self.agents),
            'agent_names': list(self.agents.keys())
        }
    
    async def shutdown(self):
        """Gracefully shutdown all agents"""
        logger.info("Shutting down SRE Agent Orchestrator...")
        
        for agent_name, agent in self.agents.items():
            try:
                if hasattr(agent, 'shutdown'):
                    await agent.shutdown()
                logger.info(f"Shutdown {agent_name} agent")
            except Exception as e:
                logger.error(f"Error shutting down {agent_name} agent: {e}")
        
        logger.info("SRE Agent Orchestrator shutdown complete")

# Example usage
if __name__ == "__main__":
    async def main():
        orchestrator = SREAgentOrchestrator()
        
        # Example log processing
        sample_log = {
            "timestamp": "2025-08-12T17:09:17.944835",
            "service": "database-primary",
            "level": "ERROR",
            "request_id": "req_40fe641a6ba2",
            "host": "database-primary-4.prod.internal",
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
        
        result = await orchestrator.process_log(sample_log)
        print(json.dumps(result, indent=2))
        
        stats = orchestrator.get_stats()
        print(f"\nStats: {stats}")
        
        await orchestrator.shutdown()
    
    asyncio.run(main()) 