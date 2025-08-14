"""
Kafka SRE Integration
====================
Integration script that connects the Kafka streaming pipeline to the SRE Agent orchestrator.
This script consumes logs from Kafka and processes them through the intelligent SRE agent system.
"""

import json
import logging
import asyncio
import signal
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import time

from kafka import KafkaConsumer
from kafka.errors import KafkaError

# Import our SRE Agent orchestrator
from sre_agent_orchestrator import SREAgentOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/sre_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class KafkaSREIntegration:
    """
    Kafka integration for SRE Agent system
    """
    
    def __init__(self, config_path: str = "config/sre_agent_config.json"):
        """
        Initialize the Kafka SRE integration
        
        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.orchestrator = None
        self.consumer = None
        self.running = False
        self.stats = {
            'messages_consumed': 0,
            'messages_processed': 0,
            'processing_errors': 0,
            'kafka_errors': 0,
            'start_time': None
        }
        
        # Create logs directory
        Path('logs').mkdir(exist_ok=True)
        
        logger.info("✅ Kafka SRE Integration initialized")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.error(f"Config file {self.config_path} not found")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise
    
    async def initialize(self):
        """Initialize the SRE Agent orchestrator and Kafka consumer"""
        try:
            # Initialize SRE Agent orchestrator
            logger.info("Initializing SRE Agent orchestrator...")
            self.orchestrator = SREAgentOrchestrator(self.config_path)
            
            # Initialize Kafka consumer
            logger.info("Initializing Kafka consumer...")
            kafka_config = self.config['kafka']
            
            self.consumer = KafkaConsumer(
                kafka_config['topic'],
                bootstrap_servers=kafka_config['bootstrap_servers'],
                group_id=kafka_config['consumer_group'],
                auto_offset_reset=kafka_config['auto_offset_reset'],
                enable_auto_commit=kafka_config['enable_auto_commit'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None
            )
            
            logger.info(f"✅ Connected to Kafka topic: {kafka_config['topic']}")
            logger.info(f"✅ Consumer group: {kafka_config['consumer_group']}")
            
        except Exception as e:
            logger.error(f"❌ Error initializing integration: {e}")
            raise
    
    async def start_consuming(self):
        """Start consuming messages from Kafka"""
        if not self.consumer or not self.orchestrator:
            raise RuntimeError("Integration not initialized")
        
        self.running = True
        self.stats['start_time'] = datetime.now()
        
        logger.info("🚀 Starting Kafka consumption...")
        
        try:
            async for message in self._message_generator():
                if not self.running:
                    break
                
                await self._process_message(message)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")
        except Exception as e:
            logger.error(f"Error in message consumption: {e}")
            self.stats['kafka_errors'] += 1
        finally:
            await self.shutdown()
    
    async def _message_generator(self):
        """Async generator for Kafka messages"""
        while self.running:
            try:
                # Get message with timeout
                message = next(self.consumer, None)
                if message:
                    yield message
                else:
                    # No message available, wait a bit
                    await asyncio.sleep(0.1)
                    
            except StopIteration:
                # No more messages
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error reading from Kafka: {e}")
                self.stats['kafka_errors'] += 1
                await asyncio.sleep(1)  # Wait before retrying
    
    async def _process_message(self, message):
        """Process a single Kafka message"""
        try:
            self.stats['messages_consumed'] += 1
            
            # Extract message data
            log_data = message.value
            topic = message.topic
            partition = message.partition
            offset = message.offset
            timestamp = message.timestamp
            
            logger.debug(f"Processing message: topic={topic}, partition={partition}, offset={offset}")
            
            # Process through SRE Agent orchestrator
            result = await self.orchestrator.process_log(log_data)
            
            # Update statistics
            self.stats['messages_processed'] += 1
            
            # Log processing result
            if result.get('error'):
                logger.error(f"Error processing log {result.get('log_id', 'unknown')}: {result['error']}")
                self.stats['processing_errors'] += 1
            else:
                logger.info(f"Processed log {result.get('log_id', 'unknown')} in {result.get('processing_time', 0):.3f}s")
                
                # Log decisions made
                decisions = result.get('decisions', [])
                for decision in decisions:
                    logger.info(f"  {decision.agent_name}: {decision.decision} (confidence: {decision.confidence:.1%})")
                
                # Log actions taken
                actions = result.get('actions_taken', [])
                for action in actions:
                    if action.get('agent') == 'rag_agent':
                        logger.info(f"  RAG Agent: {action.get('success', False)} - {action.get('playbook_used', 'Unknown')}")
                    elif action.get('agent') == 'advanced_llm_agent':
                        analysis = action.get('analysis', {})
                        logger.info(f"  Advanced LLM: {analysis.get('severity', 'unknown')} severity - {analysis.get('confidence', 0):.1%} confidence")
                    elif action.get('agent') == 'database_agent':
                        logger.info(f"  Database: Log stored successfully")
                    elif action.get('agent') == 'paging_agent':
                        logger.info(f"  Paging: Page sent - {action.get('urgency', 'unknown')} urgency")
            
            # Commit offset
            self.consumer.commit()
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.stats['processing_errors'] += 1
    
    async def shutdown(self):
        """Gracefully shutdown the integration"""
        logger.info("🛑 Shutting down Kafka SRE integration...")
        
        self.running = False
        
        try:
            # Shutdown SRE Agent orchestrator
            if self.orchestrator:
                await self.orchestrator.shutdown()
                logger.info("SRE Agent orchestrator shutdown complete")
            
            # Close Kafka consumer
            if self.consumer:
                self.consumer.close()
                logger.info("Kafka consumer closed")
            
            # Print final statistics
            self._print_final_stats()
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        logger.info("✅ Kafka SRE integration shutdown complete")
    
    def _print_final_stats(self):
        """Print final processing statistics"""
        if self.stats['start_time']:
            runtime = datetime.now() - self.stats['start_time']
            runtime_seconds = runtime.total_seconds()
            
            print("\n" + "="*60)
            print("📊 FINAL PROCESSING STATISTICS")
            print("="*60)
            print(f"Runtime: {runtime_seconds:.1f} seconds")
            print(f"Messages Consumed: {self.stats['messages_consumed']}")
            print(f"Messages Processed: {self.stats['messages_processed']}")
            print(f"Processing Errors: {self.stats['processing_errors']}")
            print(f"Kafka Errors: {self.stats['kafka_errors']}")
            
            if runtime_seconds > 0:
                throughput = self.stats['messages_processed'] / runtime_seconds
                print(f"Throughput: {throughput:.2f} messages/second")
            
            if self.stats['messages_consumed'] > 0:
                success_rate = (self.stats['messages_processed'] - self.stats['processing_errors']) / self.stats['messages_consumed']
                print(f"Success Rate: {success_rate:.1%}")
            
            # Print orchestrator stats if available
            if self.orchestrator:
                orchestrator_stats = self.orchestrator.get_stats()
                print(f"\nOrchestrator Statistics:")
                print(f"  Total Logs Processed: {orchestrator_stats.get('total_logs_processed', 0)}")
                print(f"  Anomalies Detected: {orchestrator_stats.get('anomalies_detected', 0)}")
                print(f"  Common Errors: {orchestrator_stats.get('common_errors', 0)}")
                print(f"  Uncommon Errors: {orchestrator_stats.get('uncommon_errors', 0)}")
                print(f"  Pages Sent: {orchestrator_stats.get('pages_sent', 0)}")
                print(f"  Database Stores: {orchestrator_stats.get('database_stores', 0)}")
            
            print("="*60)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        stats = self.stats.copy()
        
        if stats['start_time']:
            runtime = datetime.now() - stats['start_time']
            stats['runtime_seconds'] = runtime.total_seconds()
            
            if stats['runtime_seconds'] > 0:
                stats['throughput'] = stats['messages_processed'] / stats['runtime_seconds']
        
        if stats['messages_consumed'] > 0:
            stats['success_rate'] = (stats['messages_processed'] - stats['processing_errors']) / stats['messages_consumed']
        
        return stats

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, initiating shutdown...")
    sys.exit(0)

async def main():
    """Main function"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and run integration
    integration = KafkaSREIntegration()
    
    try:
        await integration.initialize()
        await integration.start_consuming()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚀 Starting Kafka SRE Integration...")
    print("Press Ctrl+C to stop")
    print("-" * 50)
    
    asyncio.run(main()) 