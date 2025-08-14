"""
Advanced LLM Agent
=================
Agent that handles uncommon errors using advanced LLM analysis
to generate custom solutions and recommendations.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import sqlite3
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class LLMAnalysis:
    """Represents LLM analysis result"""
    root_cause: str
    severity_assessment: str
    impact_analysis: str
    recommended_actions: List[str]
    custom_commands: List[str]
    monitoring_plan: str
    escalation_criteria: str
    confidence: float

class AdvancedLLMAgent:
    """
    Advanced LLM Agent for handling uncommon errors with sophisticated analysis
    """
    
    def __init__(self, model: str = "gpt-4", max_tokens: int = 2000, db_path: str = "data/sre_agent.db"):
        """
        Initialize the Advanced LLM Agent
        
        Args:
            model: LLM model to use for analysis
            max_tokens: Maximum tokens for LLM response
            db_path: Path to database for storing analysis history
        """
        self.model = model
        self.max_tokens = max_tokens
        self.db_path = Path(db_path)
        self.stats = {
            'total_analyzed': 0,
            'successful_analyses': 0,
            'failed_analyses': 0,
            'escalations_generated': 0
        }
        
        # Initialize database
        self._init_database()
        
        logger.info(f"✅ Advanced LLM Agent initialized with model {model}")
    
    def _init_database(self):
        """Initialize the database schema"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create LLM analysis history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS llm_analysis_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT,
                    service TEXT,
                    error_type TEXT,
                    root_cause TEXT,
                    severity TEXT,
                    recommended_actions TEXT,
                    custom_commands TEXT,
                    confidence REAL,
                    timestamp TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
    
    async def process(self, log_entry, anomaly_decision, rag_result) -> Dict[str, Any]:
        """
        Process an uncommon error using advanced LLM analysis
        
        Args:
            log_entry: LogEntry object
            anomaly_decision: Decision from anomaly detection agent
            rag_result: Result from RAG agent
            
        Returns:
            Processing result with analysis and recommendations
        """
        try:
            self.stats['total_analyzed'] += 1
            
            # Generate comprehensive context
            context = self._generate_comprehensive_context(log_entry, anomaly_decision, rag_result)
            
            # Perform LLM analysis
            analysis = await self._perform_llm_analysis(context, log_entry)
            
            # Store analysis in database
            await self._store_analysis_history(log_entry, analysis)
            
            # Generate escalation plan
            escalation_plan = self._generate_escalation_plan(analysis, log_entry)
            
            # Update statistics
            if analysis.confidence > 0.7:
                self.stats['successful_analyses'] += 1
            else:
                self.stats['failed_analyses'] += 1
            
            if analysis.severity_assessment in ['high', 'critical']:
                self.stats['escalations_generated'] += 1
            
            result = {
                'agent': 'advanced_llm_agent',
                'analysis': {
                    'root_cause': analysis.root_cause,
                    'severity': analysis.severity_assessment,
                    'impact': analysis.impact_analysis,
                    'confidence': analysis.confidence
                },
                'recommendations': {
                    'actions': analysis.recommended_actions,
                    'commands': analysis.custom_commands,
                    'monitoring': analysis.monitoring_plan
                },
                'escalation': escalation_plan,
                'metadata': {
                    'model_used': self.model,
                    'context_length': len(context),
                    'analysis_timestamp': datetime.now().isoformat()
                }
            }
            
            logger.info(f"Advanced LLM analysis: {analysis.severity_assessment} severity, {analysis.confidence:.1%} confidence")
            return result
            
        except Exception as e:
            logger.error(f"Error in advanced LLM analysis: {e}")
            return {
                'agent': 'advanced_llm_agent',
                'error': str(e),
                'analysis': {
                    'root_cause': 'Analysis failed',
                    'severity': 'unknown',
                    'impact': 'Unable to assess',
                    'confidence': 0.0
                },
                'recommendations': {
                    'actions': ['Manual intervention required'],
                    'commands': [],
                    'monitoring': 'Monitor system logs'
                },
                'escalation': {
                    'required': True,
                    'urgency': 'high',
                    'reason': f'LLM analysis failed: {str(e)}'
                }
            }
    
    def _generate_comprehensive_context(self, log_entry, anomaly_decision, rag_result) -> str:
        """Generate comprehensive context for LLM analysis"""
        context_parts = [
            "=== SRE INCIDENT ANALYSIS CONTEXT ===",
            "",
            "INCIDENT DETAILS:",
            f"Service: {log_entry.service}",
            f"Host: {log_entry.host}",
            f"Environment: {log_entry.environment}",
            f"Timestamp: {log_entry.timestamp}",
            f"Log Level: {log_entry.level}",
            f"Message: {log_entry.message or 'No message provided'}",
            "",
            "SYSTEM METRICS:",
        ]
        
        # Add metrics in a structured format
        metrics = log_entry.metrics
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                context_parts.append(f"  {key}: {value:.2f}")
            else:
                context_parts.append(f"  {key}: {value}")
        
        context_parts.extend([
            "",
            "ANOMALY DETECTION:",
            f"Decision: {anomaly_decision.decision}",
            f"Confidence: {anomaly_decision.confidence:.1%}",
            f"Reasoning: {anomaly_decision.reasoning}",
            "",
            "RAG AGENT ANALYSIS:",
            f"Decision: {rag_result.get('decision', 'unknown')}",
            f"Error Type: {rag_result.get('error_type', 'unknown')}",
            f"Reasoning: {rag_result.get('reasoning', 'No reasoning provided')}",
            f"Needs Escalation: {rag_result.get('needs_escalation', False)}",
            "",
            "ANALYSIS REQUIREMENTS:",
            "1. Identify the root cause of this incident",
            "2. Assess the severity and potential impact",
            "3. Provide specific, actionable recommendations",
            "4. Suggest custom commands or scripts if needed",
            "5. Define monitoring and escalation criteria",
            "",
            "RESPONSE FORMAT:",
            "Root Cause: [detailed explanation]",
            "Severity: [low/medium/high/critical]",
            "Impact: [potential business and technical impact]",
            "Recommended Actions: [numbered list of specific actions]",
            "Custom Commands: [specific commands or scripts]",
            "Monitoring Plan: [what to monitor and how]",
            "Escalation Criteria: [when to escalate]",
            "Confidence: [0.0-1.0]"
        ])
        
        return "\n".join(context_parts)
    
    async def _perform_llm_analysis(self, context: str, log_entry) -> LLMAnalysis:
        """Perform LLM analysis on the incident"""
        try:
            # In a real implementation, this would call an actual LLM API
            # For demo purposes, we'll simulate the analysis based on the log data
            analysis = await self._simulate_llm_analysis(context, log_entry)
            return analysis
            
        except Exception as e:
            logger.error(f"Error in LLM analysis: {e}")
            # Return fallback analysis
            return LLMAnalysis(
                root_cause="Unable to determine root cause due to analysis failure",
                severity_assessment="medium",
                impact_analysis="Potential service degradation",
                recommended_actions=["Manual investigation required"],
                custom_commands=[],
                monitoring_plan="Monitor system logs and metrics",
                escalation_criteria="If service becomes unavailable",
                confidence=0.3
            )
    
    async def _simulate_llm_analysis(self, context: str, log_entry) -> LLMAnalysis:
        """Simulate LLM analysis for demo purposes"""
        # Extract key information from log entry
        service = log_entry.service
        level = log_entry.level
        message = log_entry.message or ""
        metrics = log_entry.metrics
        
        # Analyze based on patterns
        if "database" in service.lower():
            if "connection" in message.lower() and "pool" in message.lower():
                return LLMAnalysis(
                    root_cause="Database connection pool exhaustion due to high connection demand or connection leaks",
                    severity_assessment="high",
                    impact_analysis="Service unavailability, potential data loss, cascading failures",
                    recommended_actions=[
                        "Immediately restart the database service to clear connection pool",
                        "Check for connection leaks in application code",
                        "Increase connection pool size if demand is legitimate",
                        "Monitor connection usage patterns",
                        "Implement connection pooling best practices"
                    ],
                    custom_commands=[
                        "sudo systemctl restart postgresql",
                        "sudo systemctl status postgresql",
                        "netstat -an | grep :5432 | wc -l",
                        "psql -c 'SELECT count(*) FROM pg_stat_activity;'"
                    ],
                    monitoring_plan="Monitor active connections, connection pool usage, and application response times",
                    escalation_criteria="If service restart fails or connections continue to increase",
                    confidence=0.85
                )
        
        elif "memory" in message.lower() or metrics.get('memory_usage', 0) > 90:
            return LLMAnalysis(
                root_cause="Memory exhaustion due to memory leak, high memory usage, or insufficient resources",
                severity_assessment="critical",
                impact_analysis="Service crashes, data corruption, system instability",
                recommended_actions=[
                    "Immediately restart the service to free memory",
                    "Identify memory leak sources using profiling tools",
                    "Scale up service with more memory if needed",
                    "Implement memory monitoring and alerting",
                    "Review application memory usage patterns"
                ],
                custom_commands=[
                    "sudo systemctl restart application-service",
                    "ps aux --sort=-%mem | head -10",
                    "free -h",
                    "dmesg | grep -i 'killed process'"
                ],
                monitoring_plan="Monitor memory usage, garbage collection, and application heap size",
                escalation_criteria="If memory usage continues to increase after restart",
                confidence=0.9
            )
        
        elif metrics.get('cpu_usage', 0) > 95:
            return LLMAnalysis(
                root_cause="High CPU usage due to infinite loops, inefficient algorithms, or resource contention",
                severity_assessment="high",
                impact_analysis="Service degradation, slow response times, potential cascading failures",
                recommended_actions=[
                    "Identify high CPU processes using profiling tools",
                    "Kill runaway processes if necessary",
                    "Scale up service with more CPU resources",
                    "Optimize application code and algorithms",
                    "Implement CPU usage monitoring and alerting"
                ],
                custom_commands=[
                    "ps aux --sort=-%cpu | head -10",
                    "top -p $(pgrep -f application-service)",
                    "strace -p <PID> -c",
                    "kubectl scale deployment app-deployment --replicas=3"
                ],
                monitoring_plan="Monitor CPU usage, process CPU time, and application performance metrics",
                escalation_criteria="If CPU usage remains high after process cleanup",
                confidence=0.8
            )
        
        elif metrics.get('error_rate', 0) > 0.2:
            return LLMAnalysis(
                root_cause="High error rate indicating application bugs, configuration issues, or external service failures",
                severity_assessment="high",
                impact_analysis="Poor user experience, potential data loss, service degradation",
                recommended_actions=[
                    "Review recent application logs for error patterns",
                    "Check external service dependencies",
                    "Verify configuration settings",
                    "Implement circuit breakers for external services",
                    "Roll back recent deployments if necessary"
                ],
                custom_commands=[
                    "grep -i error /var/log/application/*.log | tail -50",
                    "curl -f http://external-service/health",
                    "kubectl rollout history deployment app-deployment",
                    "kubectl rollout undo deployment app-deployment"
                ],
                monitoring_plan="Monitor error rates, application logs, and external service health",
                escalation_criteria="If error rate continues to increase or service becomes unavailable",
                confidence=0.75
            )
        
        else:
            # Generic analysis for unknown patterns
            return LLMAnalysis(
                root_cause="Unknown error pattern requiring detailed investigation",
                severity_assessment="medium",
                impact_analysis="Potential service degradation, requires investigation",
                recommended_actions=[
                    "Collect detailed system and application logs",
                    "Analyze recent changes or deployments",
                    "Check system resources and dependencies",
                    "Monitor service behavior and metrics",
                    "Prepare for potential escalation"
                ],
                custom_commands=[
                    "journalctl -u application-service --since '1 hour ago'",
                    "systemctl status application-service",
                    "netstat -tulpn | grep application-service",
                    "df -h && free -h"
                ],
                monitoring_plan="Monitor all system metrics, logs, and service health",
                escalation_criteria="If service becomes unavailable or error patterns worsen",
                confidence=0.6
            )
    
    async def _store_analysis_history(self, log_entry, analysis: LLMAnalysis):
        """Store analysis in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO llm_analysis_history 
                (request_id, service, error_type, root_cause, severity, recommended_actions, custom_commands, confidence, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                log_entry.request_id,
                log_entry.service,
                'uncommon_error',
                analysis.root_cause,
                analysis.severity_assessment,
                json.dumps(analysis.recommended_actions),
                json.dumps(analysis.custom_commands),
                analysis.confidence,
                log_entry.timestamp
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error storing analysis history: {e}")
    
    def _generate_escalation_plan(self, analysis: LLMAnalysis, log_entry) -> Dict[str, Any]:
        """Generate escalation plan based on analysis"""
        severity = analysis.severity_assessment
        confidence = analysis.confidence
        
        # Determine escalation requirements
        if severity in ['critical', 'high'] or confidence < 0.5:
            escalation_required = True
            urgency = 'high' if severity == 'critical' else 'medium'
        else:
            escalation_required = False
            urgency = 'low'
        
        escalation_plan = {
            'required': escalation_required,
            'urgency': urgency,
            'reason': f"Severity: {severity}, Confidence: {confidence:.1%}",
            'recipients': self._get_escalation_recipients(severity),
            'timeframe': self._get_escalation_timeframe(urgency),
            'instructions': analysis.escalation_criteria
        }
        
        return escalation_plan
    
    def _get_escalation_recipients(self, severity: str) -> List[str]:
        """Get escalation recipients based on severity"""
        if severity == 'critical':
            return ['oncall-sre@company.com', 'sre-manager@company.com']
        elif severity == 'high':
            return ['oncall-sre@company.com']
        else:
            return ['sre-team@company.com']
    
    def _get_escalation_timeframe(self, urgency: str) -> str:
        """Get escalation timeframe based on urgency"""
        if urgency == 'high':
            return 'immediate'
        elif urgency == 'medium':
            return 'within 15 minutes'
        else:
            return 'within 1 hour'
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            **self.stats,
            'success_rate': self.stats['successful_analyses'] / max(self.stats['total_analyzed'], 1),
            'escalation_rate': self.stats['escalations_generated'] / max(self.stats['total_analyzed'], 1)
        }
    
    async def shutdown(self):
        """Cleanup resources"""
        logger.info("Advanced LLM Agent shutdown complete")

# Example usage
if __name__ == "__main__":
    import asyncio
    from sre_agent_orchestrator import LogEntry, LogSeverity
    from agents.anomaly_detector_agent import AgentDecision
    
    async def test_agent():
        agent = AdvancedLLMAgent()
        
        # Test with uncommon error
        test_log = LogEntry(
            timestamp="2025-08-12T17:09:17.944835",
            service="custom-service",
            level="CRITICAL",
            request_id="req_test_001",
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
        
        result = await agent.process(test_log, anomaly_decision, mitigation_decision)
        print(f"Processing result: {result}")
        
        stats = agent.get_stats()
        print(f"Agent stats: {stats}")
        
        await agent.shutdown()
    
    asyncio.run(test_agent()) 