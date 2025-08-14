#!/usr/bin/env python3
"""
Paging Agent
Makes phone calls using Twilio to alert SRE on-call for critical issues
"""

import os
import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

class PagingAgent:
    def __init__(self, twilio_config=None):
        """Initialize the Paging Agent"""
        self.twilio_config = twilio_config or {
            'account_sid': os.getenv('TWILIO_ACCOUNT_SID', ''),
            'auth_token': os.getenv('TWILIO_AUTH_TOKEN', ''),
            'from_number': os.getenv('TWILIO_FROM_NUMBER', ''),
            'to_number': os.getenv('SRE_ONCALL_PHONE', '+18573357165'),
            'enabled': True
        }
        
        # Initialize Twilio client if credentials are provided
        self.twilio_client = None
        if self.twilio_config['account_sid'] and self.twilio_config['auth_token']:
            try:
                from twilio.rest import Client
                self.twilio_client = Client(
                    self.twilio_config['account_sid'], 
                    self.twilio_config['auth_token']
                )
                logger.info("✅ Twilio client initialized successfully")
            except ImportError:
                logger.warning("⚠️ Twilio library not installed. Install with: pip install twilio")
                self.twilio_client = None
            except Exception as e:
                logger.error(f"❌ Failed to initialize Twilio client: {e}")
                self.twilio_client = None
        else:
            logger.warning("⚠️ Twilio credentials not provided. Paging will be simulated.")
        
        logger.info("✅ Paging Agent initialized")
    
    async def page_sre_oncall(self, incident_data: dict) -> dict:
        """Page the SRE on-call for a critical incident"""
        try:
            # Extract incident information
            service = incident_data.get('service', 'unknown')
            request_id = incident_data.get('request_id', 'unknown')
            timestamp = incident_data.get('timestamp', datetime.now().isoformat())
            
            # Create the call message
            message = self._create_call_message(incident_data)
            
            # Make the call
            if self.twilio_client and self.twilio_config['enabled']:
                call_result = self._make_twilio_call(message)
                return {
                    'status': 'success',
                    'paging_method': 'twilio_call',
                    'call_sid': call_result.get('call_sid'),
                    'incident_id': request_id,
                    'timestamp': datetime.now().isoformat(),
                    'message': message
                }
            else:
                # Simulate the call for testing
                logger.info(f"📞 SIMULATED CALL: {message}")
                return {
                    'status': 'success',
                    'paging_method': 'simulated_call',
                    'incident_id': request_id,
                    'timestamp': datetime.now().isoformat(),
                    'message': message
                }
                
        except Exception as e:
            logger.error(f"❌ Error paging SRE on-call: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'incident_id': incident_data.get('request_id', 'unknown'),
                'timestamp': datetime.now().isoformat()
            }
    
    def _create_call_message(self, incident_data: dict) -> str:
        """Create the message for the phone call"""
        service = incident_data.get('service', 'unknown')
        request_id = incident_data.get('request_id', 'unknown')
        
        message = f"""
You have been paged for a critical issue in the system. 
Service {service} has reported an anomaly that requires immediate attention.
Please check your email at xaviers3601@gmail.com for a detailed report and recommended next steps.
Incident ID is {request_id}.
This is an automated alert from the Intelligent SRE Agent System.
"""
        return message
    
    def _make_twilio_call(self, message: str) -> dict:
        """Make a phone call using Twilio"""
        try:
            # Create the call using Twilio
            call = self.twilio_client.calls.create(
                twiml=f'<Response><Say>{message}</Say></Response>',
                to=self.twilio_config['to_number'],
                from_=self.twilio_config['from_number']
            )
            
            logger.info(f"✅ Twilio call initiated: {call.sid}")
            return {
                'call_sid': call.sid,
                'status': call.status,
                'to': call.to,
                'from_number': self.twilio_config['from_number']
            }
            
        except Exception as e:
            logger.error(f"❌ Twilio call failed: {e}")
            raise e
    
    def update_twilio_config(self, new_config: dict):
        """Update Twilio configuration"""
        self.twilio_config.update(new_config)
        
        # Reinitialize Twilio client if credentials changed
        if self.twilio_config['account_sid'] and self.twilio_config['auth_token']:
            try:
                from twilio.rest import Client
                self.twilio_client = Client(
                    self.twilio_config['account_sid'], 
                    self.twilio_config['auth_token']
                )
                logger.info("✅ Twilio client reinitialized with new credentials")
            except Exception as e:
                logger.error(f"❌ Failed to reinitialize Twilio client: {e}")
                self.twilio_client = None
        
        logger.info("✅ Twilio configuration updated")
    
    def test_call(self) -> dict:
        """Test the paging system"""
        test_incident = {
            'service': 'test-service',
            'request_id': 'test_incident_001',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info("🧪 Testing paging system...")
        return self.page_sre_oncall(test_incident) 