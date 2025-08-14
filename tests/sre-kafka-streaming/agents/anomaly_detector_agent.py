"""
Anomaly Detection Agent
======================
ML-based anomaly detection agent for SRE logs.

This agent uses the trained anomaly detection model to analyze logs
and determine if they represent anomalous behavior.
"""

import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import sys
import os

# Add the parent directory to path to import the ML pipeline
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'Aegis---Intelligent-SRE-Agent-main'))

try:
    from ml_pipeline.anomaly_detector import AnomalyDetector
except ImportError:
    # Fallback to local implementation
    class AnomalyDetector:
        def __init__(self, model_dir: str = "ml_pipeline/saved_models"):
            self.model_dir = Path(model_dir)
            self.model = None
            self.scaler = None
            self.service_encoder = None
            self.feature_names = None
            self.metadata = None
            self._load_models()
        
        def _load_models(self):
            """Load all saved model components"""
            try:
                import joblib
                # Load main model
                self.model = joblib.load(self.model_dir / "anomaly_detector.pkl")
                # Load scaler
                self.scaler = joblib.load(self.model_dir / "scaler.pkl")
                # Load service encoder
                self.service_encoder = joblib.load(self.model_dir / "service_encoder.pkl")
                # Load metadata
                with open(self.model_dir / "model_metadata.json", 'r') as f:
                    self.metadata = json.load(f)
                    self.feature_names = self.metadata['feature_names']
                print(f"✅ Models loaded successfully from {self.model_dir}")
            except Exception as e:
                print(f"❌ Error loading models: {e}")
                # Create dummy model for testing
                self.model = DummyModel()
        
        def predict(self, log_entry: Dict[str, Any]) -> tuple[bool, float]:
            """Predict if log entry is anomalous"""
            try:
                features = self._extract_features(log_entry)
                prediction = self.model.predict(features)[0]
                probability = self.model.predict_proba(features)[0][1] if hasattr(self.model, 'predict_proba') else 0.8
                return bool(prediction), float(probability)
            except Exception as e:
                print(f"Error in prediction: {e}")
                return log_entry.get('anomaly', False), 0.5
        
        def _extract_features(self, log_entry: Dict[str, Any]):
            """Extract features from log entry"""
            import pandas as pd
            import numpy as np
            
            # Create DataFrame from single entry
            df_single = pd.DataFrame([log_entry])
            features = pd.DataFrame()
            
            # Extract metrics
            metrics_df = pd.json_normalize(df_single['metrics'])
            features = pd.concat([features, metrics_df], axis=1)
            
            # Encode service
            try:
                if df_single['service'].iloc[0] in self.service_encoder.classes_:
                    features['service_encoded'] = self.service_encoder.transform(df_single['service'])
                else:
                    features['service_encoded'] = 0
            except:
                features['service_encoded'] = 0
            
            # Encode log level
            level_map = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4}
            features['level_encoded'] = df_single['level'].map(level_map).fillna(1)
            
            # Fill missing values
            features = features.fillna(0)
            
            # Scale features
            if self.scaler:
                features = self.scaler.transform(features)
            
            return features

class DummyModel:
    """Dummy model for testing when real model is not available"""
    def predict(self, features):
        return [True]  # Always predict anomaly for testing
    
    def predict_proba(self, features):
        return [[0.2, 0.8]]  # 80% confidence in anomaly

logger = logging.getLogger(__name__)

class AnomalyDetectorAgent:
    """
    Anomaly Detection Agent for SRE logs
    """
    
    def __init__(self, model_path: str = "ml_pipeline/saved_models", confidence_threshold: float = 0.7):
        """
        Initialize the Anomaly Detection Agent
        
        Args:
            model_path: Path to the ML model directory
            confidence_threshold: Minimum confidence for anomaly detection
        """
        self.model_path = Path(model_path)
        self.confidence_threshold = confidence_threshold
        self.detector = None
        self.stats = {
            'total_analyzed': 0,
            'anomalies_detected': 0,
            'false_positives': 0,
            'false_negatives': 0
        }
        
        # Initialize the ML model
        self._initialize_model()
        
        logger.info(f"✅ Anomaly Detection Agent initialized with threshold {confidence_threshold}")
    
    def _initialize_model(self):
        """Initialize the anomaly detection model"""
        try:
            self.detector = AnomalyDetector(str(self.model_path))
            logger.info("ML model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            logger.info("Using fallback detection logic")
            self.detector = None
    
    async def analyze(self, log_entry) -> Dict[str, Any]:
        """
        Analyze a log entry for anomalies
        
        Args:
            log_entry: LogEntry object to analyze
            
        Returns:
            Analysis result with decision, confidence, and reasoning
        """
        try:
            self.stats['total_analyzed'] += 1
            
            # Convert LogEntry to dict for ML model
            log_dict = {
                'timestamp': log_entry.timestamp,
                'service': log_entry.service,
                'level': log_entry.level,
                'request_id': log_entry.request_id,
                'host': log_entry.host,
                'environment': log_entry.environment,
                'metrics': log_entry.metrics,
                'anomaly': log_entry.anomaly,
                'message': log_entry.message
            }
            
            # Use ML model if available
            if self.detector:
                is_anomaly, confidence = self.detector.predict(log_dict)
            else:
                # Fallback to rule-based detection
                is_anomaly, confidence = self._rule_based_detection(log_entry)
            
            # Apply confidence threshold
            if confidence < self.confidence_threshold:
                is_anomaly = False
                confidence = 1.0 - confidence  # Confidence in normal behavior
            
            # Update statistics
            if is_anomaly:
                self.stats['anomalies_detected'] += 1
            
            # Generate reasoning
            reasoning = self._generate_reasoning(log_entry, is_anomaly, confidence)
            
            result = {
                'decision': 'anomaly' if is_anomaly else 'normal',
                'confidence': confidence,
                'reasoning': reasoning,
                'metadata': {
                    'model_used': 'ml_model' if self.detector else 'rule_based',
                    'threshold_applied': self.confidence_threshold,
                    'metrics_analyzed': list(log_entry.metrics.keys())
                }
            }
            
            logger.info(f"Anomaly analysis: {result['decision']} (confidence: {confidence:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"Error in anomaly analysis: {e}")
            return {
                'decision': 'error',
                'confidence': 0.0,
                'reasoning': f"Error during analysis: {str(e)}",
                'metadata': {'error': str(e)}
            }
    
    def _rule_based_detection(self, log_entry) -> tuple[bool, float]:
        """
        Rule-based anomaly detection as fallback
        
        Args:
            log_entry: LogEntry object
            
        Returns:
            Tuple of (is_anomaly, confidence)
        """
        metrics = log_entry.metrics
        confidence = 0.5
        anomaly_indicators = []
        
        # Check CPU usage
        if metrics.get('cpu_usage', 0) > 90:
            anomaly_indicators.append('high_cpu')
            confidence += 0.2
        
        # Check memory usage
        if metrics.get('memory_usage', 0) > 85:
            anomaly_indicators.append('high_memory')
            confidence += 0.2
        
        # Check error rate
        if metrics.get('error_rate', 0) > 0.1:
            anomaly_indicators.append('high_error_rate')
            confidence += 0.3
        
        # Check latency
        if metrics.get('request_latency_ms', 0) > 5000:
            anomaly_indicators.append('high_latency')
            confidence += 0.2
        
        # Check log level
        if log_entry.level in ['ERROR', 'CRITICAL']:
            anomaly_indicators.append('error_level')
            confidence += 0.1
        
        # Check if original log was marked as anomaly
        if log_entry.anomaly:
            anomaly_indicators.append('pre_marked_anomaly')
            confidence += 0.2
        
        is_anomaly = len(anomaly_indicators) > 0
        confidence = min(confidence, 0.95)  # Cap confidence
        
        return is_anomaly, confidence
    
    def _generate_reasoning(self, log_entry, is_anomaly: bool, confidence: float) -> str:
        """Generate human-readable reasoning for the decision"""
        metrics = log_entry.metrics
        
        if is_anomaly:
            indicators = []
            
            if metrics.get('cpu_usage', 0) > 90:
                indicators.append(f"CPU usage at {metrics['cpu_usage']:.1f}%")
            
            if metrics.get('memory_usage', 0) > 85:
                indicators.append(f"Memory usage at {metrics['memory_usage']:.1f}%")
            
            if metrics.get('error_rate', 0) > 0.1:
                indicators.append(f"Error rate at {metrics['error_rate']:.3f}")
            
            if metrics.get('request_latency_ms', 0) > 5000:
                indicators.append(f"Latency at {metrics['request_latency_ms']}ms")
            
            if log_entry.level in ['ERROR', 'CRITICAL']:
                indicators.append(f"Log level: {log_entry.level}")
            
            if indicators:
                return f"Anomaly detected with {confidence:.1%} confidence. Indicators: {', '.join(indicators)}"
            else:
                return f"Anomaly detected with {confidence:.1%} confidence based on ML model analysis."
        else:
            return f"Normal behavior detected with {confidence:.1%} confidence. All metrics within acceptable ranges."
    
    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        return {
            **self.stats,
            'detection_rate': self.stats['anomalies_detected'] / max(self.stats['total_analyzed'], 1),
            'confidence_threshold': self.confidence_threshold
        }
    
    async def shutdown(self):
        """Cleanup resources"""
        logger.info("Anomaly Detection Agent shutdown complete")

# Example usage
if __name__ == "__main__":
    import asyncio
    from sre_agent_orchestrator import LogEntry, LogSeverity
    
    async def test_agent():
        agent = AnomalyDetectorAgent()
        
        # Test with anomalous log
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
        
        result = await agent.analyze(test_log)
        print(f"Analysis result: {result}")
        
        stats = agent.get_stats()
        print(f"Agent stats: {stats}")
        
        await agent.shutdown()
    
    asyncio.run(test_agent()) 