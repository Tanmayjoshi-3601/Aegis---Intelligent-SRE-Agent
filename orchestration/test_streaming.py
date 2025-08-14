#!/usr/bin/env python3
"""
SRE Kafka Streaming Pipeline Test Script
Tests the entire pipeline by sending test logs and consuming them back
"""

import json
import time
import sys
import os
from datetime import datetime
from typing import List, Dict, Any
import logging
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError, NoBrokersAvailable
import threading
import signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Colors and emojis for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

class Emojis:
    SUCCESS = "✅"
    ERROR = "❌"
    WARNING = "⚠️"
    INFO = "ℹ️"
    ROCKET = "🚀"
    TEST = "🧪"
    SEND = "📤"
    RECEIVE = "📥"
    CHECK = "🔍"
    STATS = "📊"

class StreamingTester:
    """Test the Kafka streaming pipeline end-to-end"""
    
    def __init__(self, bootstrap_servers='localhost:9092'):
        self.bootstrap_servers = bootstrap_servers
        self.topic = 'system-logs'
        self.producer = None
        self.consumer = None
        self.test_results = {
            'producer_connected': False,
            'consumer_connected': False,
            'messages_sent': 0,
            'messages_received': 0,
            'anomalies_detected': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
        self.received_messages = []
        self.stop_consuming = False
        
    def print_status(self, status: str, message: str):
        """Print colored status messages"""
        if status == "success":
            print(f"{Colors.GREEN}{Emojis.SUCCESS} {message}{Colors.NC}")
        elif status == "error":
            print(f"{Colors.RED}{Emojis.ERROR} {message}{Colors.NC}")
        elif status == "warning":
            print(f"{Colors.YELLOW}{Emojis.WARNING} {message}{Colors.NC}")
        elif status == "info":
            print(f"{Colors.BLUE}{Emojis.INFO} {message}{Colors.NC}")
        elif status == "test":
            print(f"{Colors.PURPLE}{Emojis.TEST} {message}{Colors.NC}")
        elif status == "stats":
            print(f"{Colors.CYAN}{Emojis.STATS} {message}{Colors.NC}")
    
    def create_test_logs(self) -> List[Dict[str, Any]]:
        """Create a variety of test logs including normal and anomalous ones"""
        test_logs = []
        
        # Normal logs
        normal_services = ['api-gateway', 'user-service', 'auth-service']
        for i in range(5):
            log = {
                "timestamp": datetime.utcnow().isoformat(),
                "service": normal_services[i % len(normal_services)],
                "level": "INFO",
                "host": f"host-{i+1}",
                "metrics": {
                    "cpu_usage": 45.2 + i * 2,
                    "memory_usage": 52.1 + i * 3,
                    "error_rate": 0.002 + i * 0.001,
                    "request_latency_ms": 120 + i * 10,
                    "active_connections": 50 + i * 5
                },
                "anomaly": False,
                "message": f"Normal operation log {i+1}"
            }
            test_logs.append(log)
        
        # Anomalous logs
        anomaly_services = ['database-primary', 'cache-service', 'payment-service']
        for i in range(5):
            log = {
                "timestamp": datetime.utcnow().isoformat(),
                "service": anomaly_services[i % len(anomaly_services)],
                "level": "ERROR" if i % 2 == 0 else "WARN",
                "host": f"host-{i+6}",
                "metrics": {
                    "cpu_usage": 92.5 + i * 2,  # High CPU
                    "memory_usage": 88.1 + i * 3,  # High memory
                    "error_rate": 0.08 + i * 0.02,  # High error rate
                    "request_latency_ms": 650 + i * 50,  # High latency
                    "active_connections": 480 + i * 10  # Connection pool exhaustion
                },
                "anomaly": True,
                "message": f"Anomaly detected log {i+1}"
            }
            test_logs.append(log)
        
        return test_logs
    
    def connect_producer(self) -> bool:
        """Connect to Kafka as producer"""
        try:
            self.print_status("info", "Connecting to Kafka as producer...")
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else b'',
                retries=3,
                acks='all'
            )
            self.test_results['producer_connected'] = True
            self.print_status("success", "Producer connected successfully")
            return True
        except NoBrokersAvailable:
            self.print_status("error", "No Kafka brokers available. Is Kafka running?")
            return False
        except Exception as e:
            self.print_status("error", f"Failed to connect producer: {e}")
            return False
    
    def connect_consumer(self) -> bool:
        """Connect to Kafka as consumer"""
        try:
            self.print_status("info", "Connecting to Kafka as consumer...")
            self.consumer = KafkaConsumer(
                self.topic,
                bootstrap_servers=self.bootstrap_servers,
                auto_offset_reset='earliest',
                enable_auto_commit=True,
                group_id='test-consumer-group',
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                consumer_timeout_ms=10000  # 10 second timeout
            )
            self.test_results['consumer_connected'] = True
            self.print_status("success", "Consumer connected successfully")
            return True
        except NoBrokersAvailable:
            self.print_status("error", "No Kafka brokers available. Is Kafka running?")
            return False
        except Exception as e:
            self.print_status("error", f"Failed to connect consumer: {e}")
            return False
    
    def send_test_logs(self, logs: List[Dict[str, Any]]) -> bool:
        """Send test logs to Kafka"""
        self.print_status("info", f"Sending {len(logs)} test logs to Kafka...")
        
        try:
            for i, log in enumerate(logs):
                # Add test metadata
                log['test_metadata'] = {
                    'test_id': f"test-{i+1}",
                    'sent_at': datetime.utcnow().isoformat(),
                    'sequence': i + 1
                }
                
                # Use service name as key for partitioning
                key = log.get('service', 'unknown')
                
                future = self.producer.send(
                    self.topic,
                    key=key,
                    value=log
                )
                
                # Wait for send to complete
                record_metadata = future.get(timeout=10)
                
                self.test_results['messages_sent'] += 1
                
                if log.get('anomaly', False):
                    self.test_results['anomalies_detected'] += 1
                
                self.print_status("send", f"Sent log {i+1}/{len(logs)} - Service: {log['service']}")
                
                # Small delay between sends
                time.sleep(0.1)
            
            # Flush to ensure all messages are sent
            self.producer.flush()
            self.print_status("success", f"Successfully sent {len(logs)} test logs")
            return True
            
        except Exception as e:
            self.print_status("error", f"Error sending test logs: {e}")
            self.test_results['errors'] += 1
            return False
    
    def consume_test_logs(self, expected_count: int) -> bool:
        """Consume test logs from Kafka"""
        self.print_status("info", f"Consuming {expected_count} test logs from Kafka...")
        
        try:
            consumed_count = 0
            start_time = time.time()
            
            for message in self.consumer:
                if self.stop_consuming:
                    break
                
                log = message.value
                self.received_messages.append(log)
                consumed_count += 1
                
                # Check if this is one of our test messages
                if 'test_metadata' in log:
                    self.print_status("receive", 
                        f"Received test log {consumed_count}/{expected_count} - "
                        f"Service: {log.get('service')} - "
                        f"Anomaly: {log.get('anomaly', False)}")
                else:
                    self.print_status("warning", f"Received non-test log: {log.get('service')}")
                
                # Stop after receiving expected number of messages
                if consumed_count >= expected_count:
                    break
                
                # Timeout after 30 seconds
                if time.time() - start_time > 30:
                    self.print_status("warning", "Timeout reached while consuming messages")
                    break
            
            self.test_results['messages_received'] = consumed_count
            self.print_status("success", f"Successfully consumed {consumed_count} messages")
            return True
            
        except Exception as e:
            self.print_status("error", f"Error consuming test logs: {e}")
            self.test_results['errors'] += 1
            return False
    
    def verify_test_results(self) -> bool:
        """Verify that the test results are as expected"""
        self.print_status("info", "Verifying test results...")
        
        verification_passed = True
        
        # Check if we sent and received the same number of messages
        if self.test_results['messages_sent'] != self.test_results['messages_received']:
            self.print_status("error", 
                f"Message count mismatch: sent {self.test_results['messages_sent']}, "
                f"received {self.test_results['messages_received']}")
            verification_passed = False
        else:
            self.print_status("success", 
                f"Message count verified: {self.test_results['messages_sent']} sent and received")
        
        # Check if anomalies were properly detected
        expected_anomalies = sum(1 for log in self.received_messages if log.get('anomaly', False))
        if expected_anomalies != self.test_results['anomalies_detected']:
            self.print_status("error", 
                f"Anomaly count mismatch: expected {expected_anomalies}, "
                f"detected {self.test_results['anomalies_detected']}")
            verification_passed = False
        else:
            self.print_status("success", 
                f"Anomaly detection verified: {expected_anomalies} anomalies detected")
        
        # Check message integrity
        for i, log in enumerate(self.received_messages):
            if 'test_metadata' not in log:
                self.print_status("warning", f"Message {i+1} missing test metadata")
                continue
            
            test_id = log['test_metadata'].get('test_id')
            if not test_id or not test_id.startswith('test-'):
                self.print_status("error", f"Message {i+1} has invalid test ID: {test_id}")
                verification_passed = False
        
        # Check service distribution
        services = set(log.get('service') for log in self.received_messages)
        if len(services) < 3:  # We should have at least 3 different services
            self.print_status("warning", f"Limited service diversity: {len(services)} services")
        
        return verification_passed
    
    def print_test_summary(self):
        """Print comprehensive test summary"""
        print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
        print(f"{Colors.CYAN}{Emojis.STATS} TEST SUMMARY{Colors.NC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.NC}")
        
        # Connection status
        print(f"Producer Connected: {Emojis.SUCCESS if self.test_results['producer_connected'] else Emojis.ERROR}")
        print(f"Consumer Connected: {Emojis.SUCCESS if self.test_results['consumer_connected'] else Emojis.ERROR}")
        
        # Message statistics
        print(f"\n{Colors.BLUE}Message Statistics:{Colors.NC}")
        print(f"  Messages Sent: {self.test_results['messages_sent']}")
        print(f"  Messages Received: {self.test_results['messages_received']}")
        print(f"  Anomalies Detected: {self.test_results['anomalies_detected']}")
        print(f"  Errors: {self.test_results['errors']}")
        
        # Timing
        if self.test_results['start_time'] and self.test_results['end_time']:
            duration = self.test_results['end_time'] - self.test_results['start_time']
            print(f"  Test Duration: {duration:.2f} seconds")
        
        # Service breakdown
        if self.received_messages:
            service_counts = {}
            for log in self.received_messages:
                service = log.get('service', 'unknown')
                service_counts[service] = service_counts.get(service, 0) + 1
            
            print(f"\n{Colors.BLUE}Service Breakdown:{Colors.NC}")
            for service, count in sorted(service_counts.items()):
                print(f"  {service}: {count} logs")
        
        # Overall result
        print(f"\n{Colors.CYAN}{'='*60}{Colors.NC}")
        if (self.test_results['producer_connected'] and 
            self.test_results['consumer_connected'] and 
            self.test_results['messages_sent'] == self.test_results['messages_received'] and
            self.test_results['errors'] == 0):
            print(f"{Colors.GREEN}{Emojis.SUCCESS} ALL TESTS PASSED!{Colors.NC}")
        else:
            print(f"{Colors.RED}{Emojis.ERROR} SOME TESTS FAILED!{Colors.NC}")
        print(f"{Colors.CYAN}{'='*60}{Colors.NC}\n")
    
    def run_full_test(self) -> bool:
        """Run the complete end-to-end test"""
        self.print_status("test", "Starting SRE Kafka Streaming Pipeline Test")
        print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
        
        self.test_results['start_time'] = time.time()
        
        try:
            # Step 1: Connect producer
            if not self.connect_producer():
                return False
            
            # Step 2: Connect consumer
            if not self.connect_consumer():
                return False
            
            # Step 3: Create test logs
            test_logs = self.create_test_logs()
            self.print_status("info", f"Created {len(test_logs)} test logs")
            
            # Step 4: Send test logs
            if not self.send_test_logs(test_logs):
                return False
            
            # Step 5: Consume test logs
            if not self.consume_test_logs(len(test_logs)):
                return False
            
            # Step 6: Verify results
            verification_passed = self.verify_test_results()
            
            self.test_results['end_time'] = time.time()
            
            # Step 7: Print summary
            self.print_test_summary()
            
            return verification_passed
            
        except KeyboardInterrupt:
            self.print_status("warning", "Test interrupted by user")
            return False
        except Exception as e:
            self.print_status("error", f"Unexpected error during test: {e}")
            return False
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up connections"""
        if self.producer:
            self.producer.close()
            self.print_status("info", "Producer connection closed")
        
        if self.consumer:
            self.consumer.close()
            self.print_status("info", "Consumer connection closed")

def signal_handler(signum, frame):
    """Handle interrupt signals"""
    print(f"\n{Colors.YELLOW}{Emojis.WARNING} Test interrupted by user{Colors.NC}")
    sys.exit(0)

def main():
    """Main test function"""
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print(f"{Colors.BLUE}{Emojis.ROCKET} SRE Kafka Streaming Pipeline Test{Colors.NC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.NC}")
    
    # Check if Kafka is accessible
    tester = StreamingTester()
    
    # Run the test
    success = tester.run_full_test()
    
    if success:
        print(f"{Colors.GREEN}{Emojis.SUCCESS} Pipeline test completed successfully!{Colors.NC}")
        print(f"{Colors.GREEN}Your Kafka streaming pipeline is working correctly.{Colors.NC}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}{Emojis.ERROR} Pipeline test failed!{Colors.NC}")
        print(f"{Colors.RED}Please check your Kafka setup and try again.{Colors.NC}")
        sys.exit(1)

if __name__ == "__main__":
    main() 