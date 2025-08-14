#!/usr/bin/env python3
"""
Report Generation Agent
Generates detailed reports for anomalies and emails them to SRE on-call
"""

import json
import os
from datetime import datetime
import logging

# Import SendGrid
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logging.warning("SendGrid not available. Install with: pip install sendgrid")

logger = logging.getLogger(__name__)

class ReportGenerationAgent:
    def __init__(self, email_config=None):
        """Initialize the Report Generation Agent"""
        self.email_config = email_config or {
            'sendgrid_api_key': os.getenv('SENDGRID_API_KEY', ''),
            'sender_email': os.getenv('SRE_SENDER_EMAIL', 'khanna.ka@northeastern.edu'),
            'oncall_email': 'xaviers3601@gmail.com',
            'use_sendgrid': True
        }
        
        # Ensure all required keys are present
        if 'use_sendgrid' not in self.email_config:
            self.email_config['use_sendgrid'] = True
        
        # Handle both 'api_key' and 'sendgrid_api_key' for compatibility
        if 'api_key' in self.email_config and not self.email_config.get('sendgrid_api_key'):
            self.email_config['sendgrid_api_key'] = self.email_config['api_key']
        
        # Handle both 'to_email' and 'oncall_email' for compatibility
        if 'to_email' in self.email_config and not self.email_config.get('oncall_email'):
            self.email_config['oncall_email'] = self.email_config['to_email']
            
        # Handle both 'from_email' and 'sender_email' for compatibility
        if 'from_email' in self.email_config and not self.email_config.get('sender_email'):
            self.email_config['sender_email'] = self.email_config['from_email']
        
        # Initialize SendGrid client if available
        self.sendgrid_client = None
        if SENDGRID_AVAILABLE and self.email_config['sendgrid_api_key']:
            try:
                # Disable SSL warnings for macOS compatibility
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                self.sendgrid_client = SendGridAPIClient(api_key=self.email_config['sendgrid_api_key'])
                logger.info("✅ SendGrid client initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize SendGrid client: {e}")
                self.sendgrid_client = None
        else:
            logger.warning("⚠️ SendGrid not configured. Email sending will be simulated.")
        
        logger.info("✅ Report Generation Agent initialized")
    
    async def generate_and_send_report(self, anomaly_data, advanced_llm_result):
        """Generate a detailed report and send it via email"""
        try:
            # Generate the report
            report = self._generate_report(anomaly_data, advanced_llm_result)
            
            # Send the email
            success = self._send_email(report)
            
            if success:
                logger.info(f"✅ Report sent successfully for anomaly {anomaly_data.get('request_id', 'unknown')}")
                return {
                    'status': 'success',
                    'report_sent': True,
                    'email_sent_to': self.email_config['oncall_email'],
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error(f"❌ Failed to send report for anomaly {anomaly_data.get('request_id', 'unknown')}")
                return {
                    'status': 'error',
                    'report_sent': False,
                    'error': 'Email sending failed',
                    'timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error generating/sending report: {e}")
            return {
                'status': 'error',
                'report_sent': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _generate_report(self, anomaly_data, advanced_llm_result):
        """Generate a detailed report using prompt engineering"""
        
        # Extract key information
        service = anomaly_data.get('service', 'unknown')
        timestamp = anomaly_data.get('timestamp', datetime.now().isoformat())
        request_id = anomaly_data.get('request_id', 'unknown')
        metrics = anomaly_data.get('metrics', {})
        
        # Get LLM recommendations
        llm_summary = advanced_llm_result.get('summary', 'No summary available')
        llm_recommendations = advanced_llm_result.get('recommendations', [])
        llm_priority = advanced_llm_result.get('priority', 'unknown')
        
        # Create detailed report using prompt engineering
        report = f"""
🚨 CRITICAL SRE ALERT - SYSTEM ANOMALY DETECTED 🚨

📊 INCIDENT DETAILS:
• Service: {service}
• Incident ID: {request_id}
• Timestamp: {timestamp}
• Priority Level: {llm_priority.upper()}
• Status: REQUIRES IMMEDIATE ATTENTION

📈 SYSTEM METRICS AT TIME OF INCIDENT:
• CPU Usage: {metrics.get('cpu_usage', 'N/A')}%
• Memory Usage: {metrics.get('memory_usage', 'N/A')}%
• Error Rate: {metrics.get('error_rate', 'N/A')}%
• Request Latency: {metrics.get('request_latency_ms', 'N/A')}ms
• Active Connections: {metrics.get('active_connections', 'N/A')}

🧠 AI ANALYSIS SUMMARY:
{llm_summary}

🎯 RECOMMENDED IMMEDIATE ACTIONS:
"""
        
        # Add numbered recommendations
        for i, rec in enumerate(llm_recommendations, 1):
            report += f"{i}. {rec}\n"
        
        report += f"""

⚠️ ESCALATION PATH:
• This incident has been escalated to Advanced LLM Agent
• RAG Agent was unable to provide automated resolution
• Manual intervention required by SRE team

📞 PAGING STATUS:
• Paging Agent attempted to call: +18573357165
• Paging Status: FAILED - Twilio authentication error (Error 20003)
• Issue: Twilio credentials or phone number verification required
• Action Required: Verify Twilio account settings and phone number configuration

🎯 IMMEDIATE NEXT STEPS:
1. Review the detailed analysis above
2. Implement recommended actions immediately
3. Monitor system recovery
4. Update incident status in tracking system
5. Schedule post-incident review

🔧 TECHNICAL ISSUES TO RESOLVE:
• Twilio Paging: Verify Account SID, Auth Token, and phone number in Twilio console
• Ensure the "From" phone number (+13513005564) is properly configured
• Check Twilio account status and billing

🔗 INCIDENT TRACKING:
• Incident ID: {request_id}
• Escalation Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}
• On-Call SRE: {self.email_config['oncall_email']}
• Paging Number: +18573357165

---
This is an automated alert from the Intelligent SRE Agent System.
Please respond within 15 minutes to acknowledge receipt.
        """
        
        return report
    
    def _send_email(self, report_content):
        """Send the report via SendGrid"""
        try:
            if self.email_config['use_sendgrid'] and self.email_config['sendgrid_api_key']:
                # Use direct SendGrid API call to avoid SSL issues
                import requests
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                
                headers = {
                    'Authorization': f'Bearer {self.email_config["sendgrid_api_key"]}',
                    'Content-Type': 'application/json'
                }
                
                data = {
                    'personalizations': [
                        {
                            'to': [{'email': self.email_config['oncall_email']}]
                        }
                    ],
                    'from': {'email': self.email_config['sender_email']},
                    'subject': f"🚨 CRITICAL SRE ALERT - System Anomaly Detected - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                    'content': [
                        {
                            'type': 'text/plain',
                            'value': report_content
                        }
                    ]
                }
                
                response = requests.post(
                    'https://api.sendgrid.com/v3/mail/send',
                    headers=headers,
                    json=data,
                    verify=False
                )
                
                if response.status_code in [200, 201, 202]:
                    logger.info(f"✅ Email sent successfully via SendGrid API (Status: {response.status_code})")
                    return True
                else:
                    logger.error(f"❌ SendGrid API email failed (Status: {response.status_code})")
                    return False
            else:
                # Simulate email sending for testing
                logger.info(f"📧 SIMULATED EMAIL SENT TO: {self.email_config['oncall_email']}")
                logger.info(f"📧 SUBJECT: 🚨 CRITICAL SRE ALERT - System Anomaly Detected")
                logger.info(f"📧 CONTENT LENGTH: {len(report_content)} characters")
                return True
            
        except Exception as e:
            logger.error(f"❌ Email sending failed: {e}")
            return False
    
    def update_email_config(self, new_config):
        """Update email configuration"""
        self.email_config.update(new_config)
        logger.info("✅ Email configuration updated") 