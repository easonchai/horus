"""
Twitter monitoring agent for the Horus security monitoring system.
"""
import logging
import os
import time
from threading import Thread, Event
from typing import Dict, Any, List, Optional, Tuple

from mock.twitter_data import create_mock_tweets

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


class TwitterAgent:
    """Twitter monitoring agent for security threats."""
    
    def __init__(self, security_agent, interval=300):
        """Initialize the Twitter agent."""
        self.security_agent = security_agent
        self.interval = interval
        self.stop_event = Event()
        self.monitoring_thread = None
        
        # Set mock environment variables for Twitter only
        os.environ["TWITTER_BEARER_TOKEN"] = "mock_bearer_token"
        os.environ["TWITTER_API_KEY"] = "mock_api_key"
        os.environ["TWITTER_API_SECRET"] = "mock_api_secret"
        os.environ["TWITTER_ACCESS_TOKEN"] = "mock_access_token"
        os.environ["TWITTER_ACCESS_TOKEN_SECRET"] = "mock_access_token_secret"
        
        # Create mock tweets
        self.mock_tweets = create_mock_tweets()
        
        # Initialize the Twitter monitor
        self.twitter_monitor = self._create_twitter_monitor()
    
    def _create_twitter_monitor(self):
        """Create a TwitterSecurityMonitor instance with mock data."""
        # Import the TwitterSecurityMonitor class
        from twitter_monitor import TwitterSecurityMonitor
        
        # Create a TwitterSecurityMonitor instance with the real OpenAI client
        # passed from the SecurityAgent
        twitter_monitor = TwitterSecurityMonitor(openai_client=self.security_agent.openai_client)
        
        # Override the get_latest_tweets method to use mock data
        twitter_monitor.get_latest_tweets = lambda account_id, max_results=10: self.mock_tweets
        
        # Add a check_for_security_threats method
        twitter_monitor.check_for_security_threats = self.check_for_security_threats
        
        return twitter_monitor
    
    def check_for_security_threats(self):
        """Check for security threats in mock tweets."""
        # Filter tweets that contain "SECURITY ALERT"
        security_alerts = []
        for tweet in self.mock_tweets:
            if "SECURITY ALERT" in tweet.text:
                security_alerts.append(tweet.text)
        
        return security_alerts
    
    def start(self):
        """Start the Twitter monitoring thread."""
        print("\n" + "="*80)
        print("\033[1;36m🐦 STARTING TWITTER SECURITY MONITORING 🐦\033[0m")
        print("="*80)
        logger.info(f"Starting Twitter monitoring (interval: {self.interval} seconds)...")
        print(f"\033[1;33m[CONFIG]\033[0m Monitoring interval: {self.interval} seconds")
        print(f"\033[1;33m[CONFIG]\033[0m Mode: \033[1;35mMOCK TWITTER DATA\033[0m")
        print(f"\033[1;33m[CONFIG]\033[0m Available tweets: {len(self.mock_tweets)}")
        print("-"*80)
        
        def monitoring_loop():
            iteration = 0
            while not self.stop_event.is_set():
                try:
                    iteration += 1
                    print(f"\n\033[1;34m[MONITORING]\033[0m Iteration #{iteration} - Scanning Twitter for security threats...")
                    security_alerts = self.twitter_monitor.check_for_security_threats()
                    
                    if security_alerts:
                        alert_count = len(security_alerts)
                        print(f"\033[1;31m[ALERT]\033[0m Found {alert_count} potential security threat{'s' if alert_count > 1 else ''}!")
                        
                        for i, alert in enumerate(security_alerts, 1):
                            print("\n" + "="*80)
                            print(f"\033[1;31m🚨 SECURITY ALERT #{i}/{alert_count} DETECTED 🚨\033[0m")
                            print("="*80)
                            print(f"\033[1;33mAlert:\033[0m {alert}")
                            print("-"*80)
                            
                            # Process the security alert
                            try:
                                response = self.security_agent.process_security_alert(alert)
                                logger.info(f"Security agent response: {response[:100]}...")
                            except Exception as e:
                                logger.error(f"Error processing security alert: {str(e)}")
                                print(f"\033[1;31m[ERROR]\033[0m Failed to process security alert: {str(e)}")
                            print("="*80)
                    else:
                        print("\033[1;32m[STATUS]\033[0m No security threats found in this scan.")
                    
                    # Sleep for the specified interval
                    print(f"\033[1;34m[MONITORING]\033[0m Waiting {self.interval} seconds until next scan...")
                    for i in range(self.interval):
                        if self.stop_event.is_set():
                            break
                        if i % 60 == 0 and i > 0:
                            print(f"\033[1;34m[MONITORING]\033[0m {self.interval - i} seconds remaining until next scan...")
                        time.sleep(1)
                
                except Exception as e:
                    logger.error(f"Error in Twitter monitoring: {str(e)}")
                    print(f"\033[1;31m[ERROR]\033[0m Twitter monitoring error: {str(e)}")
                    # Sleep for a shorter interval before retrying
                    print(f"\033[1;34m[MONITORING]\033[0m Waiting 60 seconds before retry...")
                    time.sleep(60)
        
        self.monitoring_thread = Thread(target=monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        return self.monitoring_thread
    
    def stop(self):
        """Stop the Twitter monitoring thread."""
        if self.monitoring_thread:
            print("\n" + "="*80)
            print("\033[1;36m🛑 STOPPING TWITTER SECURITY MONITORING 🛑\033[0m")
            print("="*80)
            self.stop_event.set()
            self.monitoring_thread.join(timeout=5)
            print("\033[1;32m[STATUS]\033[0m Twitter monitoring stopped successfully.")
        
        return True
