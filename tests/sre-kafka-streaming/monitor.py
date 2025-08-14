#!/usr/bin/env python3
"""
SRE Kafka Streaming Pipeline Monitor
Real-time monitoring with statistics, anomaly detection, and service analysis
"""

import json
import time
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from kafka import KafkaConsumer
from kafka.errors import KafkaError, NoBrokersAvailable
import threading
import signal
from collections import defaultdict, deque
import statistics

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Reduce noise
logger = logging.getLogger(__name__)

# Colors and emojis for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    WHITE = '\033[1;37m'
    NC = '\033[0m'

class Emojis:
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    ROCKET = "🚀"
    MONITOR = "📊"
    ANOMALY = "🚨"
    SERVICE = "🔧"
    METRICS = "📈"
    ALERT = "🔔"
    CLOCK = "⏰"
    SPEED = "⚡"

class PipelineMonitor:
    """Real-time monitoring for SRE Kafka streaming pipeline"""
    
    def __init__(self, bootstrap_servers='localhost:9092'):
        self.bootstrap_servers = bootstrap_servers
        self.topic = 'system-logs'
        self.consumer = None
        self.stop_monitoring = False
        
        # Statistics tracking
        self.stats = {
            'total_logs': 0,
            'anomalies_detected': 0,
            'high_severity': 0,
            'errors': 0,
            'start_time': datetime.now(),
            'last_update': datetime.now()
        }
        
        # Service-specific tracking
        self.service_stats = defaultdict(lambda: {
            'total_logs': 0,
            'anomalies': 0,
            'high_severity': 0,
            'errors': 0,
            'avg_cpu': 0,
            'avg_memory': 0,
            'avg_error_rate': 0,
            'avg_latency': 0,
            'last_seen': None
        })
        
        # Real-time metrics (last 60 seconds)
        self.recent_logs = deque(maxlen=1000)
        self.recent_anomalies = deque(maxlen=100)
        self.recent_errors = deque(maxlen=100)
        
        # Alert tracking
        self.alerts = []
        self.alert_thresholds = {
            'anomaly_rate': 0.6,  # 60% anomaly rate triggers alert
            'error_rate': 0.1,    # 10% error rate triggers alert
            'high_cpu': 90,       # 90% CPU triggers alert
            'high_memory': 90,    # 90% memory triggers alert
            'high_latency': 1000  # 1000ms latency triggers alert
        }
        
        # Performance tracking
        self.performance_metrics = {
            'logs_per_second': deque(maxlen=60),
            'anomalies_per_second': deque(maxlen=60),
            'avg_processing_time': deque(maxlen=100)
        }
    
    def print_status(self, status: str, message: str):
        """Print colored status messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if status == "success":
            print(f"{Colors.GREEN}{Emojis.SUCCESS} [{timestamp}] {message}{Colors.NC}")
        elif status == "error":
            print(f"{Colors.RED}{Emojis.ERROR} [{timestamp}] {message}{Colors.NC}")
        elif status == "warning":
            print(f"{Colors.YELLOW}{Emojis.WARNING} [{timestamp}] {message}{Colors.NC}")
        elif status == "info":
            print(f"{Colors.BLUE}{Emojis.INFO} [{timestamp}] {message}{Colors.NC}")
        elif status == "alert":
            print(f"{Colors.RED}{Emojis.ALERT} [{timestamp}] {message}{Colors.NC}")
        elif status == "anomaly":
            print(f"{Colors.PURPLE}{Emojis.ANOMALY} [{timestamp}] {message}{Colors.NC}")
    
    def connect_consumer(self) -> bool:
        """Connect to Kafka as consumer"""
        try:
            self.print_status("info", "Connecting to Kafka for monitoring...")
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='latest',
                enable_auto_commit=True,
                group_id='sre-monitor-group',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=1000  # 1 second timeout
            )
            self.print_status("success", "Monitor connected to Kafka")
            return True
        except NoBrokersAvailable:
            self.print_status("error", "No Kafka brokers available. Is Kafka running?")
            return False
        except Exception as e:
            self.print_status("error", f"Failed to connect monitor: {e}")
            return False
    
    def process_log(self, log: Dict[str, Any]):
        """Process a single log entry for monitoring"""
        start_time = time.time()
        
        # Update basic statistics
        self.stats['total_logs'] += 1
        self.stats['last_update'] = datetime.now()
        
        # Extract service information
        service = log.get('service', 'unknown')
        service_data = self.service_stats[service]
        
        # Update service statistics
        service_data['total_logs'] += 1
        service_data['last_seen'] = datetime.now()
        
        # Check for anomalies
        is_anomaly = log.get('anomaly', False)
        if is_anomaly:
            self.stats['anomalies_detected'] += 1
            service_data['anomalies'] += 1
            self.recent_anomalies.append(log)
            self.print_status("anomaly", f"Anomaly detected in {service}")
        
        # Check streaming metadata for severity
        stream_meta = log.get('stream_metadata', {})
        analysis = stream_meta.get('analysis', {})
        
        if analysis.get('severity') == 'high':
            self.stats['high_severity'] += 1
            service_data['high_severity'] += 1
            self.trigger_alert(log, analysis)
        
        # Process metrics
        metrics = log.get('metrics', {})
        if metrics:
            # Update service averages
            service_data['avg_cpu'] = self.update_average(
                service_data['avg_cpu'], 
                metrics.get('cpu_usage', 0), 
                service_data['total_logs']
            )
            service_data['avg_memory'] = self.update_average(
                service_data['avg_memory'], 
                metrics.get('memory_usage', 0), 
                service_data['total_logs']
            )
            service_data['avg_error_rate'] = self.update_average(
                service_data['avg_error_rate'], 
                metrics.get('error_rate', 0), 
                service_data['total_logs']
            )
            service_data['avg_latency'] = self.update_average(
                service_data['avg_latency'], 
                metrics.get('request_latency_ms', 0), 
                service_data['total_logs']
            )
            
            # Check for high error rates
            if metrics.get('error_rate', 0) > 0.01:
                service_data['errors'] += 1
                self.recent_errors.append(log)
        
        # Store in recent logs
        self.recent_logs.append(log)
        
        # Update performance metrics
        processing_time = time.time() - start_time
        self.performance_metrics['avg_processing_time'].append(processing_time)
    
    def update_average(self, current_avg: float, new_value: float, count: int) -> float:
        """Update running average"""
        return (current_avg * (count - 1) + new_value) / count
    
    def trigger_alert(self, log: Dict[str, Any], analysis: Dict[str, Any]):
        """Trigger alert for high severity issues"""
        service = log.get('service', 'unknown')
        indicators = analysis.get('anomaly_indicators', [])
        metrics = log.get('metrics', {})
        
        alert = {
            'timestamp': datetime.now(),
            'service': service,
            'severity': 'high',
            'indicators': indicators,
            'metrics': {
                'cpu': metrics.get('cpu_usage', 0),
                'memory': metrics.get('memory_usage', 0),
                'error_rate': metrics.get('error_rate', 0),
                'latency': metrics.get('request_latency_ms', 0)
            }
        }
        
        self.alerts.append(alert)
        
        # Keep only recent alerts
        if len(self.alerts) > 50:
            self.alerts = self.alerts[-50:]
        
        self.print_status("alert", 
            f"HIGH SEVERITY ALERT: {service} - {', '.join(indicators)}")
    
    def calculate_recent_metrics(self) -> Dict[str, float]:
        """Calculate metrics for the last 60 seconds"""
        now = datetime.now()
        cutoff = now - timedelta(seconds=60)
        
        recent_logs = [log for log in self.recent_logs 
                      if datetime.fromisoformat(log.get('timestamp', '1970-01-01T00:00:00')) > cutoff]
        
        if not recent_logs:
            return {
                'logs_per_second': 0,
                'anomalies_per_second': 0,
                'anomaly_rate': 0
            }
        
        recent_anomalies = [log for log in recent_logs if log.get('anomaly', False)]
        
        return {
            'logs_per_second': len(recent_logs) / 60,
            'anomalies_per_second': len(recent_anomalies) / 60,
            'anomaly_rate': len(recent_anomalies) / len(recent_logs) if recent_logs else 0
        }
    
    def get_top_anomalous_services(self, limit: int = 5) -> List[tuple]:
        """Get top services with highest anomaly rates"""
        service_anomaly_rates = []
        
        for service, stats in self.service_stats.items():
            if stats['total_logs'] > 0:
                anomaly_rate = stats['anomalies'] / stats['total_logs']
                service_anomaly_rates.append((service, anomaly_rate, stats))
        
        # Sort by anomaly rate (descending)
        service_anomaly_rates.sort(key=lambda x: x[1], reverse=True)
        return service_anomaly_rates[:limit]
    
    def display_dashboard(self):
        """Display the monitoring dashboard"""
        # Clear screen (works on most terminals)
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Calculate recent metrics
        recent_metrics = self.calculate_recent_metrics()
        
        # Get top anomalous services
        top_services = self.get_top_anomalous_services()
        
        # Calculate uptime
        uptime = datetime.now() - self.stats['start_time']
        
        print(f"{Colors.CYAN}{Emojis.MONITOR} SRE KAFKA STREAMING PIPELINE MONITOR{Colors.NC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.NC}")
        print(f"{Colors.WHITE}Uptime: {uptime}{Colors.NC} | {Colors.WHITE}Last Update: {self.stats['last_update'].strftime('%H:%M:%S')}{Colors.NC}")
        print()
        
        # Overall Statistics
        print(f"{Colors.BLUE}{Emojis.STATS} OVERALL STATISTICS{Colors.NC}")
        print(f"{Colors.BLUE}{'-'*30}{Colors.NC}")
        print(f"Total Logs Processed: {self.stats['total_logs']:,}")
        print(f"Anomalies Detected: {self.stats['anomalies_detected']:,}")
        print(f"High Severity Events: {self.stats['high_severity']:,}")
        print(f"Overall Anomaly Rate: {self.stats['anomalies_detected']/max(self.stats['total_logs'], 1)*100:.2f}%")
        print()
        
        # Real-time Metrics
        print(f"{Colors.PURPLE}{Emojis.SPEED} REAL-TIME METRICS (Last 60s){Colors.NC}")
        print(f"{Colors.PURPLE}{'-'*35}{Colors.NC}")
        print(f"Logs/Second: {recent_metrics['logs_per_second']:.1f}")
        print(f"Anomalies/Second: {recent_metrics['anomalies_per_second']:.1f}")
        print(f"Anomaly Rate: {recent_metrics['anomaly_rate']*100:.1f}%")
        
        if self.performance_metrics['avg_processing_time']:
            avg_processing = statistics.mean(self.performance_metrics['avg_processing_time'])
            print(f"Avg Processing Time: {avg_processing*1000:.2f}ms")
        print()
        
        # Top Anomalous Services
        print(f"{Colors.YELLOW}{Emojis.SERVICE} TOP ANOMALOUS SERVICES{Colors.NC}")
        print(f"{Colors.YELLOW}{'-'*35}{Colors.NC}")
        if top_services:
            for i, (service, anomaly_rate, stats) in enumerate(top_services, 1):
                status_emoji = Emojis.ANOMALY if anomaly_rate > 0.5 else Emojis.WARNING if anomaly_rate > 0.2 else Emojis.INFO
                print(f"{i}. {service}")
                print(f"   Anomaly Rate: {anomaly_rate*100:.1f}% {status_emoji}")
                print(f"   Total Logs: {stats['total_logs']:,}")
                print(f"   Avg CPU: {stats['avg_cpu']:.1f}% | Avg Memory: {stats['avg_memory']:.1f}%")
                print(f"   Avg Error Rate: {stats['avg_error_rate']*100:.2f}% | Avg Latency: {stats['avg_latency']:.0f}ms")
                print()
        else:
            print("No services with anomalies detected yet.")
        print()
        
        # Recent Alerts
        print(f"{Colors.RED}{Emojis.ALERT} RECENT ALERTS (Last 10){Colors.NC}")
        print(f"{Colors.RED}{'-'*30}{Colors.NC}")
        recent_alerts = self.alerts[-10:] if self.alerts else []
        if recent_alerts:
            for alert in recent_alerts:
                timestamp = alert['timestamp'].strftime('%H:%M:%S')
                service = alert['service']
                indicators = ', '.join(alert['indicators'])
                print(f"[{timestamp}] {service}: {indicators}")
        else:
            print("No recent alerts.")
        print()
        
        # Service Health Summary
        print(f"{Colors.GREEN}{Emojis.INFO} SERVICE HEALTH SUMMARY{Colors.NC}")
        print(f"{Colors.GREEN}{'-'*30}{Colors.NC}")
        healthy_services = 0
        warning_services = 0
        critical_services = 0
        
        for service, stats in self.service_stats.items():
            if stats['total_logs'] > 0:
                anomaly_rate = stats['anomalies'] / stats['total_logs']
                if anomaly_rate < 0.1:
                    healthy_services += 1
                elif anomaly_rate < 0.5:
                    warning_services += 1
                else:
                    critical_services += 1
        
        print(f"Healthy: {healthy_services} {Emojis.SUCCESS}")
        print(f"Warning: {warning_services} {Emojis.WARNING}")
        print(f"Critical: {critical_services} {Emojis.ERROR}")
        print()
        
        # Footer
        print(f"{Colors.CYAN}{'='*60}{Colors.NC}")
        print(f"{Colors.WHITE}Press Ctrl+C to stop monitoring{Colors.NC}")
        print(f"{Colors.WHITE}Kafka UI: http://localhost:8080{Colors.NC}")
    
    def monitor_stream(self):
        """Start monitoring the Kafka stream"""
        self.print_status("info", "Starting real-time monitoring...")
        
        try:
            while not self.stop_monitoring:
                # Process messages with timeout
                try:
                    for message in self.consumer:
                        if self.stop_monitoring:
                            break
                        
                        log = message.value
                        self.process_log(log)
                        
                        # Update display every 10 logs or every 2 seconds
                        if self.stats['total_logs'] % 10 == 0 or \
                           (datetime.now() - self.stats['last_update']).seconds >= 2:
                            self.display_dashboard()
                        
                except Exception as e:
                    if not self.stop_monitoring:
                        self.print_status("error", f"Error processing message: {e}")
                        time.sleep(1)
            
        except KeyboardInterrupt:
            self.print_status("warning", "Monitoring stopped by user")
        except Exception as e:
            self.print_status("error", f"Monitoring error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up connections"""
        if self.consumer:
            self.consumer.close()
            self.print_status("info", "Monitor connection closed")

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print(f"\n{Colors.YELLOW}{Emojis.WARNING} Monitor interrupted by user{Colors.NC}")
    sys.exit(0)

def main():
    """Main monitoring function"""
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print(f"{Colors.CYAN}{Emojis.ROCKET} SRE Kafka Streaming Pipeline Monitor{Colors.NC}")
    print(f"{Colors.CYAN}{'='*60}{Colors.NC}")
    
    # Create and start monitor
    monitor = PipelineMonitor()
    
    # Connect to Kafka
    if not monitor.connect_consumer():
        print(f"{Colors.RED}{Emojis.ERROR} Failed to connect to Kafka{Colors.NC}")
        print(f"{Colors.RED}Please ensure Kafka is running and accessible{Colors.NC}")
        sys.exit(1)
    
    # Start monitoring
    try:
        monitor.monitor_stream()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}{Emojis.WARNING} Monitor stopped{Colors.NC}")
    except Exception as e:
        print(f"{Colors.RED}{Emojis.ERROR} Monitor error: {e}{Colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main() 