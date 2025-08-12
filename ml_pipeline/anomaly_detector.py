"""
Anomaly Detector Module for SRE Agent
======================================
Production-ready module for anomaly detection inference.

Usage:
    from ml_pipeline.anomaly_detector import AnomalyDetector
    
    detector = AnomalyDetector()
    is_anomaly, confidence = detector.predict(log_entry)
"""

import json
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from typing import Dict, Tuple, Any, List
from datetime import datetime


class AnomalyDetector:
    """
    Anomaly detection model for SRE logs
    """
    
    def __init__(self, model_dir: str = "ml_pipeline/saved_models"):
        """
        Initialize the anomaly detector
        
        Args:
            model_dir: Directory containing saved models
        """
        self.model_dir = Path(model_dir)
        self.model = None
        self.scaler = None
        self.service_encoder = None
        self.feature_names = None
        self.metadata = None
        
        # Load all components
        self._load_models()
        
    def _load_models(self):
        """Load all saved model components"""
        try:
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
            print(f"   Model type: {self.metadata['model_type']}")
            print(f"   Features: {self.metadata['n_features']}")
            print(f"   Training F1-Score: {self.metadata['performance']['f1_score']:.3f}")
            
        except Exception as e:
            print(f"❌ Error loading models: {e}")
            raise
    
    def _extract_features(self, log_entry: Dict[str, Any]) -> pd.DataFrame:
        """
        Extract features from a log entry
        
        Args:
            log_entry: Dictionary containing log data
            
        Returns:
            DataFrame with extracted features
        """
        # Create DataFrame from single entry
        df_single = pd.DataFrame([log_entry])
        features = pd.DataFrame()
        
        # 1. Extract metrics
        metrics_df = pd.json_normalize(df_single['metrics'])
        features = pd.concat([features, metrics_df], axis=1)
        
        # 2. Encode service
        try:
            if df_single['service'].iloc[0] in self.service_encoder.classes_:
                features['service_encoded'] = self.service_encoder.transform(df_single['service'])
            else:
                # Unknown service - use most common encoding
                features['service_encoded'] = 0
        except:
            features['service_encoded'] = 0
        
        # 3. Encode log level
        level_map = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3, 'CRITICAL': 4}
        features['level_encoded'] = df_single['level'].map(level_map).fillna(1)  # Default to INFO
        
        # 4. Time features
        df_single['timestamp'] = pd.to_datetime(df_single['timestamp'])
        features['hour'] = df_single['timestamp'].dt.hour
        features['day_of_week'] = df_single['timestamp'].dt.dayofweek
        features['is_weekend'] = (features['day_of_week'] >= 5).astype(int)
        
        # 5. Composite features
        features['cpu_memory_product'] = features['cpu_usage'] * features['memory_usage'] / 100
        features['system_load'] = (features['cpu_usage'] + features['memory_usage'] + features['disk_usage']) / 3
        features['network_imbalance'] = abs(features['network_in_mbps'] - features['network_out_mbps'])
        features['latency_to_rps_ratio'] = features['request_latency_ms'] / (features['requests_per_second'] + 1)
        
        # 6. Binary flags
        features['has_user_id'] = df_single['user_id'].notna().astype(int)
        features['has_transaction_id'] = df_single['transaction_id'].notna().astype(int)
        
        # 7. Statistical flags
        features['high_cpu_flag'] = (features['cpu_usage'] > 80).astype(int)
        features['high_memory_flag'] = (features['memory_usage'] > 80).astype(int)
        features['high_error_flag'] = (features['error_rate'] > 0.05).astype(int)
        
        # Ensure all features are present (fill missing with 0)
        for feature in self.feature_names:
            if feature not in features.columns:
                features[feature] = 0
        
        return features[self.feature_names]
    
    def predict(self, log_entry: Dict[str, Any]) -> Tuple[bool, float]:
        """
        Predict if a log entry is an anomaly
        
        Args:
            log_entry: Dictionary containing log data
            
        Returns:
            Tuple of (is_anomaly: bool, confidence: float)
        """
        try:
            # Extract features
            features = self._extract_features(log_entry)
            
            # Scale features
            features_scaled = self.scaler.transform(features)
            
            # Make prediction
            prediction = self.model.predict(features_scaled)[0]
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            # Get confidence for the predicted class
            confidence = probabilities[prediction]
            
            # Return boolean anomaly flag and confidence
            is_anomaly = bool(prediction == 1)
            
            return is_anomaly, float(confidence)
            
        except Exception as e:
            print(f"Error during prediction: {e}")
            # Return safe default (not anomaly, low confidence)
            return False, 0.0
    
    def predict_batch(self, log_entries: List[Dict[str, Any]]) -> List[Tuple[bool, float]]:
        """
        Predict anomalies for multiple log entries
        
        Args:
            log_entries: List of log entry dictionaries
            
        Returns:
            List of (is_anomaly, confidence) tuples
        """
        results = []
        for log_entry in log_entries:
            results.append(self.predict(log_entry))
        return results
    
    def get_anomaly_score(self, log_entry: Dict[str, Any]) -> float:
        """
        Get anomaly probability score (0-1)
        
        Args:
            log_entry: Dictionary containing log data
            
        Returns:
            Anomaly probability (0 = normal, 1 = definitely anomaly)
        """
        try:
            features = self._extract_features(log_entry)
            features_scaled = self.scaler.transform(features)
            probabilities = self.model.predict_proba(features_scaled)[0]
            
            # Return probability of being an anomaly
            return float(probabilities[1])
            
        except Exception as e:
            print(f"Error getting anomaly score: {e}")
            return 0.0
    
    def explain_prediction(self, log_entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Provide explanation for why a log was classified as anomaly
        
        Args:
            log_entry: Dictionary containing log data
            
        Returns:
            Dictionary with prediction details and key indicators
        """
        is_anomaly, confidence = self.predict(log_entry)
        anomaly_score = self.get_anomaly_score(log_entry)
        
        # Identify key anomaly indicators
        metrics = log_entry.get('metrics', {})
        indicators = []
        
        if metrics.get('cpu_usage', 0) > 85:
            indicators.append(f"High CPU: {metrics['cpu_usage']:.1f}%")
        if metrics.get('memory_usage', 0) > 85:
            indicators.append(f"High Memory: {metrics['memory_usage']:.1f}%")
        if metrics.get('error_rate', 0) > 0.1:
            indicators.append(f"High Error Rate: {metrics['error_rate']:.2%}")
        if metrics.get('request_latency_ms', 0) > 1000:
            indicators.append(f"High Latency: {metrics['request_latency_ms']}ms")
        if metrics.get('disk_usage', 0) > 90:
            indicators.append(f"High Disk: {metrics['disk_usage']:.1f}%")
        
        return {
            'is_anomaly': is_anomaly,
            'confidence': confidence,
            'anomaly_score': anomaly_score,
            'service': log_entry.get('service', 'unknown'),
            'level': log_entry.get('level', 'unknown'),
            'indicators': indicators if indicators else ['No obvious indicators - check pattern analysis'],
            'timestamp': log_entry.get('timestamp', ''),
            'recommendation': self._get_recommendation(is_anomaly, indicators)
        }
    
    def _get_recommendation(self, is_anomaly: bool, indicators: List[str]) -> str:
        """Generate recommendation based on prediction"""
        if not is_anomaly:
            return "No action required - system operating normally"
        
        if any('CPU' in ind for ind in indicators):
            return "Investigate CPU usage - consider scaling horizontally"
        elif any('Memory' in ind for ind in indicators):
            return "Check for memory leaks - consider service restart"
        elif any('Error Rate' in ind for ind in indicators):
            return "High error rate detected - check recent deployments"
        elif any('Latency' in ind for ind in indicators):
            return "Performance degradation - check database and network"
        elif any('Disk' in ind for ind in indicators):
            return "Disk space critical - clean up logs and temporary files"
        else:
            return "Anomaly detected - investigate service health"


# Standalone function for quick testing
def quick_test():
    """Quick test of the anomaly detector"""
    
    # Sample log entry
    test_log = {
        "timestamp": datetime.now().isoformat(),
        "service": "api-gateway",
        "level": "ERROR",
        "request_id": "req_test123",
        "host": "api-gateway-1.prod.internal",
        "environment": "production",
        "metrics": {
            "cpu_usage": 92.5,
            "memory_usage": 88.3,
            "disk_usage": 75.0,
            "network_in_mbps": 45.2,
            "network_out_mbps": 38.7,
            "active_connections": 892,
            "request_latency_ms": 2500,
            "requests_per_second": 450,
            "error_rate": 0.15
        },
        "message": "Connection timeout after 30000ms",
        "user_id": "user_1234",
        "transaction_id": "tx_abc123"
    }
    
    # Initialize detector
    detector = AnomalyDetector()
    
    # Make prediction
    is_anomaly, confidence = detector.predict(test_log)
    
    # Get detailed explanation
    explanation = detector.explain_prediction(test_log)
    
    print("\n" + "="*50)
    print("ANOMALY DETECTION TEST")
    print("="*50)
    print(f"Service: {test_log['service']}")
    print(f"Level: {test_log['level']}")
    print(f"CPU: {test_log['metrics']['cpu_usage']:.1f}%")
    print(f"Memory: {test_log['metrics']['memory_usage']:.1f}%")
    print(f"Latency: {test_log['metrics']['request_latency_ms']}ms")
    print(f"\nPrediction: {'🚨 ANOMALY' if is_anomaly else '✅ NORMAL'}")
    print(f"Confidence: {confidence:.2%}")
    print(f"Anomaly Score: {explanation['anomaly_score']:.3f}")
    print(f"\nIndicators:")
    for ind in explanation['indicators']:
        print(f"  - {ind}")
    print(f"\nRecommendation: {explanation['recommendation']}")
    print("="*50)


if __name__ == "__main__":
    # Run quick test when module is executed directly
    quick_test()