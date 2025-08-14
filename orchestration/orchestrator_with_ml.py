"""
ML-Enhanced Intelligent SRE Orchestrator
=========================================
This orchestrator:
1. Uses ML model for anomaly detection instead of thresholds
2. Keeps the docker exec approach for Kafka (working solution)
3. Routes logs based on ML predictions
4. Provides detailed anomaly explanations
"""

import json
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from orchestration.config import KAFKA_CONFIG, STORAGE_CONFIG, ML_CONFIG, AGENT_CONFIG

# Import ML model
try:
    from ml_pipeline.anomaly_detector import AnomalyDetector
    ML_AVAILABLE = True
except ImportError:
    print("⚠️ ML model not found. Falling back to threshold-based detection.")
    ML_AVAILABLE = False

class MLOrchestrator:
    """
    ML-Enhanced orchestrator that uses trained model for anomaly detection
    """
    
    def __init__(self):
        """Initialize the orchestrator with ML model"""
        print("🤖 Starting ML-Enhanced SRE Orchestrator")
        print(f"   Kafka: {KAFKA_CONFIG['bootstrap_servers']}")
        print(f"   Topic: {KAFKA_CONFIG['topics']['input']}")
        print("-" * 60)
        
        self.stats = {
            'total_logs': 0,
            'ml_anomalies': 0,
            'ml_normal': 0,
            'high_confidence_alerts': 0,  # confidence > 0.8
            'medium_confidence_alerts': 0,  # confidence 0.5-0.8
            'low_confidence_alerts': 0,  # confidence < 0.5
            'ml_errors': 0,
            'start_time': datetime.now()
        }
        
        # Initialize storage paths from config
        self.storage_config = STORAGE_CONFIG
        self.ml_config = ML_CONFIG
        self.agent_config = AGENT_CONFIG
        
        # Initialize ML model
        self._init_ml_model()
        
        # Check Kafka
        self._check_kafka()
    
    def _init_ml_model(self):
        """Initialize the ML anomaly detection model"""
        if ML_AVAILABLE:
            try:
                print("🧠 Loading ML model...")
                self.ml_detector = AnomalyDetector()
                print("✅ ML model loaded successfully!")
                self.use_ml = True
            except Exception as e:
                print(f"⚠️ Error loading ML model: {e}")
                print("   Falling back to threshold-based detection")
                self.ml_detector = None
                self.use_ml = False
        else:
            self.ml_detector = None
            self.use_ml = False
            print("⚠️ Using threshold-based detection (ML not available)")
    
    def _check_kafka(self):
        """Check if Kafka is running"""
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=sre-kafka", "--format", "{{.Names}}"],
                capture_output=True,
                text=True
            )
            if "sre-kafka" not in result.stdout:
                print("❌ Kafka is not running!")
                print("Please start Kafka first:")
                print("cd sre-kafka-streaming && docker-compose up -d zookeeper kafka kafka-ui && cd ..")
                sys.exit(1)
            print("✅ Kafka is running")
        except Exception as e:
            print(f"❌ Error checking Kafka: {e}")
            sys.exit(1)
    
    def detect_anomaly_ml(self, log_data):
        """
        Use ML model to detect anomalies
        Returns: (is_anomaly, confidence, explanation)
        """
        if not self.use_ml or not self.ml_detector:
            return self.detect_anomaly_threshold(log_data)
        
        try:
            # Check if log has required fields for ML model
            if 'metrics' not in log_data:
                print(f"⚠️ Log missing 'metrics' field, using threshold detection")
                return self.detect_anomaly_threshold(log_data)
            
            # Preprocess log data to match ML model expectations
            preprocessed_log = self._preprocess_log_for_ml(log_data)
            
            # ML-based detection
            is_anomaly, confidence = self.ml_detector.predict(preprocessed_log)
            
            # Get detailed explanation if anomaly
            explanation = None
            if is_anomaly:
                try:
                    explanation = self.ml_detector.explain_prediction(preprocessed_log)
                except Exception as e:
                    print(f"⚠️ Error getting explanation: {e}")
                    explanation = {"anomaly_score": confidence, "confidence": confidence}
            
            return is_anomaly, confidence, explanation
            
        except Exception as e:
            self.stats['ml_errors'] += 1
            print(f"⚠️ ML detection error: {e}")
            # Fallback to threshold-based
            return self.detect_anomaly_threshold(log_data)
    
    def detect_anomaly_threshold(self, log_data):
        """
        Fallback threshold-based detection
        Returns: (is_anomaly, confidence, explanation)
        """
        metrics = log_data.get('metrics', {})
        level = log_data.get('level', 'INFO')
        
        is_anomaly = False
        confidence = 0.0
        indicators = []
        
        # Check thresholds
        if metrics.get('cpu_usage', 0) > 80:
            is_anomaly = True
            confidence = max(confidence, 0.7)
            indicators.append(f"High CPU: {metrics['cpu_usage']:.1f}%")
        
        if metrics.get('memory_usage', 0) > 85:
            is_anomaly = True
            confidence = max(confidence, 0.8)
            indicators.append(f"High Memory: {metrics['memory_usage']:.1f}%")
        
        if metrics.get('error_rate', 0) > 0.1:
            is_anomaly = True
            confidence = max(confidence, 0.9)
            indicators.append(f"High Error Rate: {metrics['error_rate']:.2%}")
        
        if level in ['ERROR', 'CRITICAL']:
            is_anomaly = True
            confidence = max(confidence, 0.85)
            indicators.append(f"Error Level: {level}")
        
        explanation = {
            'anomaly_score': confidence,
            'confidence': confidence,
            'indicators': indicators,
            'recommendation': self._get_recommendation(indicators)
        } if is_anomaly else None
        
        return is_anomaly, confidence, explanation
    
    def _preprocess_log_for_ml(self, log_data):
        """
        Preprocess log data to match ML model expectations
        Adds missing fields that the ML model was trained on
        """
        # Create a copy to avoid modifying original
        preprocessed = log_data.copy()
        
        # Add missing fields that ML model expects
        if 'user_id' not in preprocessed:
            preprocessed['user_id'] = None
        
        if 'transaction_id' not in preprocessed:
            preprocessed['transaction_id'] = None
        
        if 'request_id' not in preprocessed:
            preprocessed['request_id'] = None
        
        if 'host' not in preprocessed:
            preprocessed['host'] = f"{preprocessed.get('service', 'unknown')}-host"
        
        if 'environment' not in preprocessed:
            preprocessed['environment'] = 'production'
        
        if 'anomaly' not in preprocessed:
            preprocessed['anomaly'] = False
        
        # Ensure metrics has all expected fields
        metrics = preprocessed.get('metrics', {})
        expected_metrics = [
            'cpu_usage', 'memory_usage', 'disk_usage', 
            'network_in_mbps', 'network_out_mbps', 'active_connections',
            'request_latency_ms', 'requests_per_second', 'error_rate'
        ]
        
        for metric in expected_metrics:
            if metric not in metrics:
                # Set reasonable defaults
                if metric == 'cpu_usage':
                    metrics[metric] = 50.0
                elif metric == 'memory_usage':
                    metrics[metric] = 60.0
                elif metric == 'disk_usage':
                    metrics[metric] = 70.0
                elif metric in ['network_in_mbps', 'network_out_mbps']:
                    metrics[metric] = 50.0
                elif metric == 'active_connections':
                    metrics[metric] = 200
                elif metric == 'request_latency_ms':
                    metrics[metric] = 100
                elif metric == 'requests_per_second':
                    metrics[metric] = 500
                elif metric == 'error_rate':
                    metrics[metric] = 0.01
        
        preprocessed['metrics'] = metrics
        
        return preprocessed
    
    def _get_recommendation(self, indicators):
        """Generate recommendation based on indicators"""
        if any('CPU' in ind for ind in indicators):
            return "Check CPU usage - consider scaling horizontally"
        elif any('Memory' in ind for ind in indicators):
            return "Check for memory leaks - consider service restart"
        elif any('Error Rate' in ind for ind in indicators):
            return "High error rate - check recent deployments"
        else:
            return "Investigate service health and logs"
    
    def process_log(self, log_data):
        """
        Process a single log entry with ML detection
        """
        self.stats['total_logs'] += 1
        
        # Extract key fields
        service = log_data.get('service', 'unknown')
        level = log_data.get('level', 'INFO')
        message = log_data.get('message', '')
        timestamp = log_data.get('timestamp', 'N/A')
        
        # ML-based anomaly detection
        is_anomaly, confidence, explanation = self.detect_anomaly_ml(log_data)
        
        if is_anomaly:
            self.stats['ml_anomalies'] += 1
            
            # Categorize by confidence
            if confidence > 0.8:
                self.stats['high_confidence_alerts'] += 1
                alert_level = "🚨 HIGH"
                color = "\033[91m"  # Red
            elif confidence > 0.5:
                self.stats['medium_confidence_alerts'] += 1
                alert_level = "⚠️  MEDIUM"
                color = "\033[93m"  # Yellow
            else:
                self.stats['low_confidence_alerts'] += 1
                alert_level = "📊 LOW"
                color = "\033[94m"  # Blue
            
            # Display anomaly alert
            print(f"\n{color}{alert_level} CONFIDENCE ANOMALY DETECTED\033[0m")
            print(f"   Service: {service}")
            print(f"   Level: {level}")
            print(f"   Confidence: {confidence:.1%}")
            
            if explanation:
                print(f"   Score: {explanation.get('anomaly_score', 0):.3f}")
                indicators = explanation.get('indicators', [])
                if indicators:
                    print(f"   Indicators:")
                    for ind in indicators[:3]:
                        print(f"      • {ind}")
                recommendation = explanation.get('recommendation', '')
                if recommendation:
                    print(f"   💡 Recommendation: {recommendation}")
            
            print(f"   Message: {message[:80]}...")
            print("-" * 60)
            
            # Save as anomaly
            self._save_log(log_data, 'anomaly', confidence, explanation)
        else:
            self.stats['ml_normal'] += 1
            # Normal log - just show progress
            if self.stats['total_logs'] % 10 == 0:
                print(f"📊 Processed {self.stats['total_logs']} logs | Anomalies: {self.stats['ml_anomalies']} | Normal: {self.stats['ml_normal']}")
            
            # Save as normal
            self._save_log(log_data, 'normal', confidence, None)
        
        # Show detailed stats every 25 logs
        if self.stats['total_logs'] % 25 == 0:
            self._show_stats()
    
    def _show_stats(self):
        """Show current ML processing statistics"""
        runtime = datetime.now() - self.stats['start_time']
        rate = self.stats['total_logs'] / runtime.total_seconds() if runtime.total_seconds() > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"📊 ML ORCHESTRATOR STATISTICS")
        print(f"{'='*60}")
        print(f"   Total logs processed: {self.stats['total_logs']}")
        print(f"   ML Anomalies detected: {self.stats['ml_anomalies']}")
        print(f"   Normal logs: {self.stats['ml_normal']}")
        print(f"   Anomaly rate: {(self.stats['ml_anomalies']/self.stats['total_logs']*100) if self.stats['total_logs'] > 0 else 0:.1f}%")
        print(f"   \n   Confidence Distribution:")
        print(f"      High (>80%): {self.stats['high_confidence_alerts']}")
        print(f"      Medium (50-80%): {self.stats['medium_confidence_alerts']}")
        print(f"      Low (<50%): {self.stats['low_confidence_alerts']}")
        print(f"   \n   ML errors: {self.stats['ml_errors']}")
        print(f"   Processing rate: {rate:.2f} logs/sec")
        print(f"   Using: {'ML Model' if self.use_ml else 'Threshold Detection'}")
        print(f"{'='*60}\n")
    
    def _save_log(self, log_data, log_type, confidence, explanation):
        """Save log with ML detection results"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_id = f"{timestamp}_{self.stats['total_logs']}"
            
            # Add ML results to log
            log_data['ml_analysis'] = {
                'detected_as': log_type,
                'confidence': confidence,
                'analyzed_at': datetime.now().isoformat(),
                'model_used': 'ml' if self.use_ml else 'threshold'
            }
            
            if explanation:
                log_data['ml_analysis']['explanation'] = explanation
            
            # Determine storage path
            if log_type == 'anomaly':
                storage_path = self.storage_config['anomaly_logs']
                filename = f"anomaly_{log_id}_conf{int(confidence*100)}.json"
            else:
                storage_path = self.storage_config['normal_logs']
                filename = f"normal_{log_id}.json"
            
            # Save the log
            log_file = storage_path / filename
            with open(log_file, 'w') as f:
                json.dump(log_data, f, indent=2)
                
        except Exception as e:
            print(f"❌ Error saving log: {e}")
    
    def run(self):
        """Main orchestration loop using docker exec"""
        print("\n👂 ML Orchestrator listening for logs... (Press Ctrl+C to stop)\n")
        
        try:
            # Read logs from Kafka using docker exec
            cmd = [
                "docker", "exec", "-i", "sre-kafka",
                "kafka-console-consumer",
                "--bootstrap-server", KAFKA_CONFIG['bootstrap_servers'],
                "--topic", KAFKA_CONFIG['topics']['input'],
                "--from-beginning",
                "--group", "ml-orchestrator-group",  # Different group to avoid conflicts
                "--max-messages", "1"  # Read one message at a time
            ]
            
            while True:
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0 and result.stdout.strip():
                        lines = result.stdout.strip().split('\n')
                        
                        for line in lines:
                            if line.strip():
                                try:
                                    log_data = json.loads(line.strip())
                                    self.process_log(log_data)
                                except json.JSONDecodeError as e:
                                    continue
                    else:
                        time.sleep(1)
                        
                except subprocess.TimeoutExpired:
                    continue
                except Exception as e:
                    print(f"❌ Error processing log: {e}")
                    time.sleep(5)
        
        except KeyboardInterrupt:
            print("\n\n⚠️ Shutting down ML Orchestrator...")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Clean shutdown with final ML statistics"""
        runtime = datetime.now() - self.stats['start_time']
        
        print("\n" + "=" * 70)
        print("🤖 ML ORCHESTRATOR - FINAL STATISTICS")
        print("=" * 70)
        print(f"Runtime: {runtime}")
        print(f"Total Logs Processed: {self.stats['total_logs']}")
        print(f"\n📊 ML Detection Results:")
        print(f"   Anomalies Detected: {self.stats['ml_anomalies']}")
        print(f"   Normal Logs: {self.stats['ml_normal']}")
        
        if self.stats['total_logs'] > 0:
            anomaly_rate = (self.stats['ml_anomalies'] / self.stats['total_logs']) * 100
            print(f"   Anomaly Rate: {anomaly_rate:.2f}%")
        
        print(f"\n🎯 Confidence Distribution:")
        print(f"   High Confidence (>80%): {self.stats['high_confidence_alerts']}")
        print(f"   Medium Confidence (50-80%): {self.stats['medium_confidence_alerts']}")
        print(f"   Low Confidence (<50%): {self.stats['low_confidence_alerts']}")
        
        if self.stats['ml_errors'] > 0:
            print(f"\n⚠️ ML Errors encountered: {self.stats['ml_errors']}")
        
        if self.stats['total_logs'] > 0:
            rate = self.stats['total_logs'] / runtime.total_seconds()
            print(f"\n⚡ Average Processing Rate: {rate:.2f} logs/second")
        
        print(f"\n🧠 Detection Method: {'ML Model' if self.use_ml else 'Threshold-based (fallback)'}")
        print("=" * 70)
        
        # Show storage information
        print(f"\n📁 Logs saved to:")
        print(f"   Normal logs: {self.storage_config['normal_logs']}")
        print(f"   Anomaly logs: {self.storage_config['anomaly_logs']}")
        
        print("\n✅ ML Orchestrator shutdown complete!")


if __name__ == "__main__":
    # Run the ML-enhanced orchestrator
    orchestrator = MLOrchestrator()
    orchestrator.run()