# streaming/kafka/custom_log_streamer.py
"""
Custom Kafka streaming implementation for your specific log format
"""
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomLogStreamer:
    """Streams your custom format logs through Kafka"""
    
    def __init__(self, bootstrap_servers='localhost:9092'):
        self.bootstrap_servers = bootstrap_servers
        self.topic = 'system-logs'
        self.producer = None
        self.consumer = None
        self.metadata = None
        self.logs = []
        self.stats = {
            'total_sent': 0,
            'anomalies_sent': 0,
            'scenarios_triggered': 0,
            'errors': 0
        }
        
    def load_logs(self, log_file_path: str, metadata_file_path: str):
        """Load logs and metadata from your generated files"""
        try:
            # Load metadata
            with open(metadata_file_path, 'r') as f:
                self.metadata = json.load(f)
            logger.info(f"Loaded metadata: {self.metadata['total_logs']} total logs")
            logger.info(f"Scenarios: {len(self.metadata['scenarios'])} scenarios")
            
            # Load logs
            with open(log_file_path, 'r') as f:
                # Your logs seem to be in a specific format, parsing accordingly
                content = f.read()
                # If logs are in JSON array format
                if content.strip().startswith('['):
                    self.logs = json.loads(content)
                else:
                    # If logs are newline-delimited JSON
                    self.logs = []
                    for line in content.strip().split('\n'):
                        if line.strip():
                            try:
                                self.logs.append(json.loads(line))
                            except:
                                pass
                                
            logger.info(f"Loaded {len(self.logs)} logs from file")
            return True
            
        except Exception as e:
            logger.error(f"Error loading logs: {e}")
            return False
    
    def connect_producer(self):
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else b'',
                compression_type='gzip',
                batch_size=16384,
                linger_ms=10,
                retries=3
            )
            logger.info("Producer connected to Kafka")
            return True
        except Exception as e:
            logger.error(f"Failed to connect producer: {e}")
            return False
    
    def analyze_log(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze log for anomalies based on your data structure"""
        analysis = {
            'is_anomaly': log.get('anomaly', False),
            'severity': 'normal',
            'anomaly_indicators': []
        }
        
        metrics = log.get('metrics', {})
        
        # Check for high resource usage
        if metrics.get('cpu_usage', 0) > 85:
            analysis['anomaly_indicators'].append('high_cpu')
            analysis['severity'] = 'high'
            
        if metrics.get('memory_usage', 0) > 85:
            analysis['anomaly_indicators'].append('high_memory')
            analysis['severity'] = 'high'
            
        if metrics.get('error_rate', 0) > 0.05:  # 5% error rate
            analysis['anomaly_indicators'].append('high_error_rate')
            analysis['severity'] = 'medium'
            
        if metrics.get('request_latency_ms', 0) > 500:
            analysis['anomaly_indicators'].append('high_latency')
            analysis['severity'] = 'medium'
            
        # Check for connection pool issues
        if metrics.get('active_connections', 0) > 450:
            analysis['anomaly_indicators'].append('connection_pool_exhaustion')
            analysis['severity'] = 'high'
        
        # Override with explicit anomaly flag from data
        if log.get('anomaly', False):
            analysis['is_anomaly'] = True
            if not analysis['anomaly_indicators']:
                analysis['anomaly_indicators'].append('flagged_anomaly')
            if analysis['severity'] == 'normal':
                analysis['severity'] = 'medium'
                
        return analysis
    
    def enhance_log_for_streaming(self, log: Dict[str, Any]) -> Dict[str, Any]:
        """Add streaming metadata to log"""
        enhanced = log.copy()
        enhanced['stream_metadata'] = {
            'streamed_at': datetime.utcnow().isoformat(),
            'stream_sequence': self.stats['total_sent'],
            'producer_id': 'custom-streamer-001',
            'analysis': self.analyze_log(log)
        }
        return enhanced
    
    def stream_normal_mode(self, logs: List[Dict], rate: int = 10):
        """Stream logs at a constant rate"""
        logger.info(f"Streaming {len(logs)} logs at {rate} logs/second")
        interval = 1.0 / rate
        
        for log in logs:
            enhanced_log = self.enhance_log_for_streaming(log)
            
            try:
                # Use service name as key for partitioning
                key = log.get('service', 'unknown')
                
                future = self.producer.send(
                    self.topic,
                    key=key,
                    value=enhanced_log
                )
                
                self.stats['total_sent'] += 1
                if enhanced_log['stream_metadata']['analysis']['is_anomaly']:
                    self.stats['anomalies_sent'] += 1
                
                # Log progress every 100 logs
                if self.stats['total_sent'] % 100 == 0:
                    logger.info(f"Progress: {self.stats['total_sent']}/{len(logs)} logs sent "
                              f"({self.stats['anomalies_sent']} anomalies)")
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error sending log: {e}")
                self.stats['errors'] += 1
        
        # Final flush
        self.producer.flush()
        logger.info(f"Streaming complete: {self.stats}")
    
    def stream_scenario_mode(self, scenario_type: str):
        """Stream logs based on specific scenarios from metadata"""
        scenario_logs = []
        
        # Find scenario in metadata
        for scenario in self.metadata.get('scenarios', []):
            if scenario['type'] == scenario_type:
                logger.info(f"Found scenario: {scenario}")
                # In a real implementation, you'd filter logs by timestamp
                # For now, we'll simulate by taking a subset
                scenario_logs = self.logs[:scenario['log_count']]
                break
        
        if not scenario_logs:
            logger.warning(f"No logs found for scenario: {scenario_type}")
            return
        
        logger.info(f"Streaming {scenario_type} scenario with {len(scenario_logs)} logs")
        
        # Adjust rate based on scenario
        if scenario_type == 'ddos_attack':
            # Very high rate for DDoS
            self.stream_burst_mode(scenario_logs, burst_rate=100, burst_duration=10)
        elif scenario_type == 'memory_leak':
            # Gradual increase for memory leak
            self.stream_gradual_increase(scenario_logs)
        elif scenario_type == 'cascading_failure':
            # Mixed pattern for cascading failure
            self.stream_cascade_pattern(scenario_logs)
        else:
            self.stream_normal_mode(scenario_logs)
    
    def stream_burst_mode(self, logs: List[Dict], burst_rate: int = 50, burst_duration: int = 5):
        """Stream logs with burst pattern (for DDoS simulation)"""
        logger.info(f"Burst mode: {burst_rate} logs/sec for {burst_duration} seconds")
        
        burst_interval = 1.0 / burst_rate
        normal_interval = 0.5  # Normal rate between bursts
        
        burst_end_time = time.time() + burst_duration
        
        for i, log in enumerate(logs):
            enhanced_log = self.enhance_log_for_streaming(log)
            
            # Determine if we're in burst period
            if time.time() < burst_end_time:
                interval = burst_interval
                enhanced_log['stream_metadata']['burst_mode'] = True
            else:
                interval = normal_interval
                enhanced_log['stream_metadata']['burst_mode'] = False
            
            try:
                self.producer.send(
                    self.topic,
                    key=log.get('service', 'unknown'),
                    value=enhanced_log
                )
                self.stats['total_sent'] += 1
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in burst mode: {e}")
                self.stats['errors'] += 1
        
        self.producer.flush()
    
    def stream_gradual_increase(self, logs: List[Dict]):
        """Stream with gradually increasing rate (memory leak simulation)"""
        logger.info("Gradual increase mode: simulating memory leak")
        
        initial_rate = 5
        max_rate = 30
        increase_factor = 1.05
        
        current_rate = initial_rate
        
        for i, log in enumerate(logs):
            enhanced_log = self.enhance_log_for_streaming(log)
            
            # Gradually increase memory usage in metrics
            if 'metrics' in enhanced_log:
                base_memory = enhanced_log['metrics'].get('memory_usage', 50)
                enhanced_log['metrics']['memory_usage'] = min(base_memory * (1 + i * 0.01), 99)
            
            enhanced_log['stream_metadata']['pattern'] = 'gradual_increase'
            enhanced_log['stream_metadata']['current_rate'] = current_rate
            
            try:
                self.producer.send(
                    self.topic,
                    key=log.get('service', 'unknown'),
                    value=enhanced_log
                )
                self.stats['total_sent'] += 1
                
                # Sleep based on current rate
                time.sleep(1.0 / current_rate)
                
                # Increase rate
                current_rate = min(current_rate * increase_factor, max_rate)
                
            except Exception as e:
                logger.error(f"Error in gradual increase: {e}")
                self.stats['errors'] += 1
        
        self.producer.flush()
    
    def stream_cascade_pattern(self, logs: List[Dict]):
        """Stream cascading failure pattern"""
        logger.info("Cascade pattern: simulating cascading failure")
        
        # Start with one service failing, then cascade to others
        affected_services = []
        
        for i, log in enumerate(logs):
            enhanced_log = self.enhance_log_for_streaming(log)
            
            # First 20% - single service failure
            if i < len(logs) * 0.2:
                if not affected_services:
                    affected_services.append(log.get('service', 'unknown'))
                if log.get('service') in affected_services:
                    enhanced_log['stream_metadata']['cascade_stage'] = 'initial_failure'
                    enhanced_log['anomaly'] = True
                    
            # Next 40% - cascade to related services
            elif i < len(logs) * 0.6:
                if random.random() > 0.5:
                    service = log.get('service', 'unknown')
                    if service not in affected_services:
                        affected_services.append(service)
                if log.get('service') in affected_services:
                    enhanced_log['stream_metadata']['cascade_stage'] = 'spreading'
                    enhanced_log['anomaly'] = True
                    
            # Final 40% - system-wide impact
            else:
                enhanced_log['stream_metadata']['cascade_stage'] = 'system_wide'
                if random.random() > 0.3:
                    enhanced_log['anomaly'] = True
            
            try:
                self.producer.send(
                    self.topic,
                    key=log.get('service', 'unknown'),
                    value=enhanced_log
                )
                self.stats['total_sent'] += 1
                
                # Variable rate based on cascade stage
                if enhanced_log.get('anomaly'):
                    time.sleep(0.05)  # Faster for anomalies
                else:
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error in cascade pattern: {e}")
                self.stats['errors'] += 1
        
        self.producer.flush()
        logger.info(f"Cascade affected services: {affected_services}")
    
    def stream_realistic_pattern(self):
        """Stream logs following realistic patterns from metadata"""
        logger.info("Starting realistic streaming based on metadata scenarios")
        
        # Group logs by timestamp if available
        logs_by_time = {}
        for log in self.logs:
            timestamp = log.get('timestamp', 'unknown')
            if timestamp not in logs_by_time:
                logs_by_time[timestamp] = []
            logs_by_time[timestamp].append(log)
        
        # Sort timestamps
        sorted_times = sorted(logs_by_time.keys())
        
        logger.info(f"Streaming {len(sorted_times)} unique timestamps")
        
        # Stream in chronological order
        for timestamp in sorted_times:
            logs_batch = logs_by_time[timestamp]
            
            for log in logs_batch:
                enhanced_log = self.enhance_log_for_streaming(log)
                
                try:
                    self.producer.send(
                        self.topic,
                        key=log.get('service', 'unknown'),
                        value=enhanced_log
                    )
                    self.stats['total_sent'] += 1
                    
                    if log.get('anomaly', False):
                        self.stats['anomalies_sent'] += 1
                    
                except Exception as e:
                    logger.error(f"Error streaming log: {e}")
                    self.stats['errors'] += 1
            
            # Batch delay
            time.sleep(0.1)
            
            # Flush periodically
            if self.stats['total_sent'] % 100 == 0:
                self.producer.flush()
                logger.info(f"Progress: {self.stats['total_sent']} logs sent")
        
        # Final flush
        self.producer.flush()
        logger.info(f"Realistic streaming complete: {self.stats}")
    
    def print_stats(self):
        """Print streaming statistics"""
        print("\n" + "="*50)
        print("STREAMING STATISTICS")
        print("="*50)
        print(f"Total Logs Sent: {self.stats['total_sent']}")
        print(f"Anomalies Sent: {self.stats['anomalies_sent']}")
        print(f"Anomaly Rate: {self.stats['anomalies_sent']/max(self.stats['total_sent'], 1)*100:.2f}%")
        print(f"Errors: {self.stats['errors']}")
        print(f"Services: {len(set(log.get('service', 'unknown') for log in self.logs[:self.stats['total_sent']]))}")
        print("="*50 + "\n")
    
    def close(self):
        """Close connections"""
        if self.producer:
            self.producer.close()
            logger.info("Producer closed")

# Consumer for processing your custom logs
class CustomLogConsumer:
    """Consumes and processes your custom format logs"""
    
    def __init__(self, bootstrap_servers='localhost:9092'):
        self.bootstrap_servers = bootstrap_servers
        self.topic = 'system-logs'
        self.consumer = None
        self.stats = {
            'total_consumed': 0,
            'anomalies_detected': 0,
            'high_severity': 0,
            'by_service': {}
        }
    
    def connect(self):
        """Connect to Kafka as consumer"""
        try:
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='sre-agent-consumer',
                value_deserializer=lambda m: json.loads(m.decode('utf-8'))
            )
            logger.info("Consumer connected to Kafka")
            return True
        except Exception as e:
            logger.error(f"Failed to connect consumer: {e}")
            return False
    
    def process_log(self, log: Dict[str, Any]):
        """Process a single log entry"""
        self.stats['total_consumed'] += 1
        
        # Extract service
        service = log.get('service', 'unknown')
        if service not in self.stats['by_service']:
            self.stats['by_service'][service] = {
                'count': 0,
                'anomalies': 0,
                'errors': 0
            }
        
        self.stats['by_service'][service]['count'] += 1
        
        # Check for anomalies
        if log.get('anomaly', False):
            self.stats['anomalies_detected'] += 1
            self.stats['by_service'][service]['anomalies'] += 1
            
        # Check streaming metadata if available
        stream_meta = log.get('stream_metadata', {})
        analysis = stream_meta.get('analysis', {})
        
        if analysis.get('severity') == 'high':
            self.stats['high_severity'] += 1
            self.trigger_alert(log, analysis)
        
        # Check metrics
        metrics = log.get('metrics', {})
        if metrics.get('error_rate', 0) > 0.01:
            self.stats['by_service'][service]['errors'] += 1
        
        # Log progress
        if self.stats['total_consumed'] % 100 == 0:
            self.print_stats()
    
    def trigger_alert(self, log: Dict[str, Any], analysis: Dict[str, Any]):
        """Trigger alert for high severity issues"""
        logger.warning(f"🚨 HIGH SEVERITY ALERT!")
        logger.warning(f"  Service: {log.get('service')}")
        logger.warning(f"  Host: {log.get('host')}")
        logger.warning(f"  Indicators: {analysis.get('anomaly_indicators')}")
        logger.warning(f"  Metrics: CPU={log.get('metrics', {}).get('cpu_usage', 0):.1f}%, "
                      f"Memory={log.get('metrics', {}).get('memory_usage', 0):.1f}%")
    
    def consume_stream(self):
        """Start consuming logs from Kafka"""
        logger.info("Starting to consume logs...")
        
        try:
            for message in self.consumer:
                log = message.value
                self.process_log(log)
                
        except KeyboardInterrupt:
            logger.info("Consumer interrupted by user")
        except Exception as e:
            logger.error(f"Consumer error: {e}")
        finally:
            self.print_stats()
    
    def print_stats(self):
        """Print consumption statistics"""
        print("\n" + "="*50)
        print("CONSUMPTION STATISTICS")
        print("="*50)
        print(f"Total Consumed: {self.stats['total_consumed']}")
        print(f"Anomalies Detected: {self.stats['anomalies_detected']}")
        print(f"High Severity: {self.stats['high_severity']}")
        print(f"Detection Rate: {self.stats['anomalies_detected']/max(self.stats['total_consumed'], 1)*100:.2f}%")
        print("\nBy Service:")
        for service, data in sorted(self.stats['by_service'].items(), 
                                   key=lambda x: x[1]['anomalies'], reverse=True)[:5]:
            print(f"  {service}: {data['count']} logs, {data['anomalies']} anomalies")
        print("="*50 + "\n")

# Main execution script
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Stream custom logs through Kafka")
    parser.add_argument("--mode", choices=["produce", "consume"], required=True,
                       help="Run as producer or consumer")
    parser.add_argument("--logs", default="logs.json", help="Path to logs file")
    parser.add_argument("--metadata", default="metadata.json", help="Path to metadata file")
    parser.add_argument("--rate", type=int, default=10, help="Logs per second")
    parser.add_argument("--scenario", choices=["normal", "ddos_attack", "memory_leak", 
                                               "cascading_failure", "realistic"],
                       default="normal", help="Streaming scenario")
    
    args = parser.parse_args()
    
    if args.mode == "produce":
        # Producer mode
        streamer = CustomLogStreamer()
        
        # Load logs
        if not streamer.load_logs(args.logs, args.metadata):
            exit(1)
        
        # Connect to Kafka
        if not streamer.connect_producer():
            exit(1)
        
        # Stream based on scenario
        try:
            if args.scenario == "realistic":
                streamer.stream_realistic_pattern()
            elif args.scenario in ["ddos_attack", "memory_leak", "cascading_failure"]:
                streamer.stream_scenario_mode(args.scenario)
            else:
                streamer.stream_normal_mode(streamer.logs, args.rate)
                
            streamer.print_stats()
            
        except KeyboardInterrupt:
            logger.info("Streaming interrupted")
        finally:
            streamer.close()
            
    else:
        # Consumer mode
        consumer = CustomLogConsumer()
        
        if not consumer.connect():
            exit(1)
            
        consumer.consume_stream()
