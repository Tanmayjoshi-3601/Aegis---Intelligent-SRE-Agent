#!/usr/bin/env python3
"""
SRE Application - Kafka Streaming Integration
============================================

This module integrates the SRE application with the Kafka streaming pipeline
for real-time log analysis and anomaly detection.

Features:
- Stream logs from your application to Kafka
- Real-time anomaly detection using your ML models
- Integration with existing log formats
- Monitoring and alerting capabilities
"""

import json
import time
import asyncio
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
import threading
from dataclasses import dataclass

# Kafka imports
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

# ML Pipeline imports
import sys
sys.path.append('ml_pipeline')
from anomaly_detector import AnomalyDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class StreamingConfig:
    """Configuration for streaming pipeline"""
    kafka_bootstrap_servers: str = 'localhost:9092'
    kafka_topic: str = 'system-logs'
    streaming_rate: int = 10  # logs per second
    batch_size: int = 100
    enable_ml_analysis: bool = True
    enable_monitoring: bool = True
    log_source_path: str = 'data/synthetic/streaming/logs.json'
    metadata_path: str = 'data/synthetic/streaming/metadata.json'

class SREStreamingService:
    """
    Main streaming service that integrates your SRE application with Kafka
    """
    
    def __init__(self, config: StreamingConfig):
        self.config = config
        self.producer = None
        self.consumer = None
        self.anomaly_detector = None
        self.logs = []
        self.metadata = {}
        self.is_running = False
        self.stats = {
            'total_sent': 0,
            'anomalies_detected': 0,
            'errors': 0,
            'start_time': None,
            'last_log_time': None
        }
        
        # Initialize components
        self._load_logs()
        self._initialize_ml_pipeline()
        self._connect_kafka()
    
    def _load_logs(self):
        """Load logs from the streaming data folder"""
        try:
            # Load metadata
            with open(self.config.metadata_path, 'r') as f:
                self.metadata = json.load(f)
            logger.info(f"Loaded metadata: {self.metadata.get('total_logs', 0)} total logs")
            
            # Load logs
            with open(self.config.log_source_path, 'r') as f:
                content = f.read().strip()
                if content.startswith('['):
                    self.logs = json.loads(content)
                else:
                    # Handle newline-delimited JSON
                    self.logs = []
                    for line in content.split('\n'):
                        if line.strip():
                            try:
                                self.logs.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
            
            logger.info(f"Loaded {len(self.logs)} logs for streaming")
            
        except Exception as e:
            logger.error(f"Error loading logs: {e}")
            raise
    
    def _initialize_ml_pipeline(self):
        """Initialize the ML anomaly detection pipeline"""
        if self.config.enable_ml_analysis:
            try:
                self.anomaly_detector = AnomalyDetector()
                logger.info("ML pipeline initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize ML pipeline: {e}")
                self.config.enable_ml_analysis = False
    
    def _connect_kafka(self):
        """Connect to Kafka producer and consumer"""
        try:
            # Initialize producer
            self.producer = KafkaProducer(
                bootstrap_servers=self.config.kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else b'',
                compression_type='gzip',
                batch_size=16384,
                linger_ms=10,
                retries=3,
                api_version=(2, 5, 0),  # Explicit API version
                request_timeout_ms=30000,
                connections_max_idle_ms=10000
            )
            logger.info("✅ Kafka producer connected")
            
            # Initialize consumer for real-time analysis
            self.consumer = KafkaConsumer(
                self.config.kafka_topic,
                bootstrap_servers=self.config.kafka_bootstrap_servers,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='sre-analysis-group',
                api_version=(2, 5, 0)  # Explicit API version
            )
            logger.info("✅ Kafka consumer connected")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to Kafka: {e}")
            raise
    
    def enhance_log(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance log with streaming metadata and ML analysis"""
        enhanced = log.copy()
        
        # Add streaming metadata
        enhanced['stream_metadata'] = {
            'streamed_at': datetime.utcnow().isoformat(),
            'stream_sequence': self.stats['total_sent'],
            'producer_id': 'sre-app-streamer',
            'source': 'sre-application'
        }
        
        # Add ML analysis if enabled
        if self.config.enable_ml_analysis and self.anomaly_detector:
            try:
                # Extract features for ML analysis
                features = self._extract_features(log)
                prediction = self.anomaly_detector.predict_single(features)
                
                enhanced['ml_analysis'] = {
                    'predicted_anomaly': prediction['is_anomaly'],
                    'confidence': prediction.get('confidence', 0.0),
                    'anomaly_type': prediction.get('anomaly_type', 'unknown'),
                    'analysis_timestamp': datetime.utcnow().isoformat()
                }
                
                if prediction['is_anomaly']:
                    self.stats['anomalies_detected'] += 1
                    logger.warning(f"🚨 Anomaly detected in {log.get('service', 'unknown')}: {prediction.get('anomaly_type', 'unknown')}")
                    
            except Exception as e:
                logger.error(f"ML analysis failed: {e}")
                enhanced['ml_analysis'] = {
                    'error': str(e),
                    'analysis_timestamp': datetime.utcnow().isoformat()
                }
        
        return enhanced
    
    def _extract_features(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features from log for ML analysis"""
        metrics = log.get('metrics', {})
        
        features = {
            'cpu_usage': metrics.get('cpu_usage', 0.0),
            'memory_usage': metrics.get('memory_usage', 0.0),
            'error_rate': metrics.get('error_rate', 0.0),
            'request_latency_ms': metrics.get('request_latency_ms', 0.0),
            'active_connections': metrics.get('active_connections', 0.0),
            'service': log.get('service', 'unknown'),
            'level': log.get('level', 'INFO')
        }
        
        return features
    
    def stream_logs(self, mode: str = 'normal', duration_minutes: int = None):
        """
        Stream logs to Kafka
        
        Args:
            mode: 'normal', 'burst', or 'scenario'
            duration_minutes: Optional duration limit
        """
        if self.is_running:
            logger.warning("Streaming already in progress")
            return
        
        self.is_running = True
        self.stats['start_time'] = datetime.utcnow()
        logger.info(f"🚀 Starting log streaming in {mode} mode")
        
        try:
            if mode == 'normal':
                self._stream_normal_mode(duration_minutes)
            elif mode == 'burst':
                self._stream_burst_mode(duration_minutes)
            elif mode == 'scenario':
                self._stream_scenario_mode(duration_minutes)
            else:
                raise ValueError(f"Unknown streaming mode: {mode}")
                
        except KeyboardInterrupt:
            logger.info("🛑 Streaming interrupted by user")
        except Exception as e:
            logger.error(f"❌ Streaming error: {e}")
        finally:
            self.is_running = False
            self._cleanup()
    
    def _stream_normal_mode(self, duration_minutes: int = None):
        """Stream logs at normal rate"""
        interval = 1.0 / self.config.streaming_rate
        end_time = None
        
        if duration_minutes:
            end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
            logger.info(f"Streaming for {duration_minutes} minutes")
        
        for i, log in enumerate(self.logs):
            if not self.is_running or (end_time and datetime.utcnow() >= end_time):
                break
            
            enhanced_log = self.enhance_log(log)
            
            try:
                # Use service name as key for partitioning
                key = log.get('service', 'unknown')
                
                future = self.producer.send(
                    self.config.kafka_topic,
                    key=key,
                    value=enhanced_log
                )
                
                # Wait for send to complete
                record_metadata = future.get(timeout=10)
                
                self.stats['total_sent'] += 1
                self.stats['last_log_time'] = datetime.utcnow()
                
                # Log progress
                if self.stats['total_sent'] % 100 == 0:
                    self._log_progress()
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error sending log: {e}")
                self.stats['errors'] += 1
        
        # Final flush
        self.producer.flush()
        logger.info(f"✅ Normal streaming complete: {self.stats}")
    
    def _stream_burst_mode(self, duration_minutes: int = None):
        """Stream logs in bursts to simulate high load"""
        burst_size = 50
        burst_interval = 5  # seconds between bursts
        
        end_time = None
        if duration_minutes:
            end_time = datetime.utcnow() + timedelta(minutes=duration_minutes)
        
        while self.is_running and (not end_time or datetime.utcnow() < end_time):
            logger.info(f"🔥 Streaming burst of {burst_size} logs")
            
            # Stream burst
            for i in range(min(burst_size, len(self.logs) - self.stats['total_sent'])):
                if not self.is_running:
                    break
                
                log = self.logs[self.stats['total_sent'] % len(self.logs)]
                enhanced_log = self.enhance_log(log)
                
                try:
                    key = log.get('service', 'unknown')
                    future = self.producer.send(
                        self.config.kafka_topic,
                        key=key,
                        value=enhanced_log
                    )
                    future.get(timeout=5)
                    
                    self.stats['total_sent'] += 1
                    
                except Exception as e:
                    logger.error(f"Error in burst: {e}")
                    self.stats['errors'] += 1
            
            self.producer.flush()
            self._log_progress()
            
            # Wait before next burst
            time.sleep(burst_interval)
    
    def _stream_scenario_mode(self, duration_minutes: int = None):
        """Stream logs based on specific scenarios"""
        # This would implement scenario-based streaming
        # For now, we'll use normal mode
        logger.info("Scenario mode not yet implemented, using normal mode")
        self._stream_normal_mode(duration_minutes)
    
    def _log_progress(self):
        """Log streaming progress"""
        elapsed = datetime.utcnow() - self.stats['start_time']
        rate = self.stats['total_sent'] / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
        
        logger.info(
            f"📊 Progress: {self.stats['total_sent']} logs sent, "
            f"{self.stats['anomalies_detected']} anomalies, "
            f"{self.stats['errors']} errors, "
            f"Rate: {rate:.1f} logs/sec"
        )
    
    def start_real_time_analysis(self):
        """Start real-time analysis of incoming logs"""
        logger.info("🔍 Starting real-time log analysis")
        
        def analyze_logs():
            try:
                for message in self.consumer:
                    if not self.is_running:
                        break
                    
                    log = message.value
                    logger.info(f"📝 Analyzing log from {log.get('service', 'unknown')}")
                    
                    # Additional real-time analysis can be added here
                    # For example, alerting, dashboard updates, etc.
                    
            except Exception as e:
                logger.error(f"Analysis error: {e}")
        
        # Start analysis in separate thread
        analysis_thread = threading.Thread(target=analyze_logs, daemon=True)
        analysis_thread.start()
        logger.info("✅ Real-time analysis started")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current streaming statistics"""
        stats = self.stats.copy()
        if stats['start_time']:
            elapsed = datetime.utcnow() - stats['start_time']
            stats['elapsed_seconds'] = elapsed.total_seconds()
            stats['rate_logs_per_sec'] = stats['total_sent'] / elapsed.total_seconds() if elapsed.total_seconds() > 0 else 0
        
        return stats
    
    def _cleanup(self):
        """Cleanup resources"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
        
        if self.consumer:
            self.consumer.close()
        
        logger.info("🧹 Cleanup completed")

def main():
    """Main function to run the streaming service"""
    import argparse
    
    parser = argparse.ArgumentParser(description='SRE Application Streaming Service')
    parser.add_argument('--mode', choices=['normal', 'burst', 'scenario'], default='normal',
                       help='Streaming mode')
    parser.add_argument('--duration', type=int, help='Duration in minutes')
    parser.add_argument('--rate', type=int, default=10, help='Logs per second')
    parser.add_argument('--kafka-servers', default='localhost:9092', help='Kafka bootstrap servers')
    parser.add_argument('--topic', default='system-logs', help='Kafka topic')
    parser.add_argument('--no-ml', action='store_true', help='Disable ML analysis')
    
    args = parser.parse_args()
    
    # Create configuration
    config = StreamingConfig(
        kafka_bootstrap_servers=args.kafka_servers,
        kafka_topic=args.topic,
        streaming_rate=args.rate,
        enable_ml_analysis=not args.no_ml
    )
    
    # Create and run streaming service
    service = SREStreamingService(config)
    
    try:
        # Start real-time analysis
        service.start_real_time_analysis()
        
        # Start streaming
        service.stream_logs(mode=args.mode, duration_minutes=args.duration)
        
    except KeyboardInterrupt:
        logger.info("🛑 Service stopped by user")
    except Exception as e:
        logger.error(f"❌ Service error: {e}")
    finally:
        service.is_running = False
        service._cleanup()

if __name__ == "__main__":
    main()
