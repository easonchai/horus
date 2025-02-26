"""
Twitter monitoring agent for the Horus security monitoring system.
"""
import logging
import os
import time
from threading import Thread, Event
from typing import Dict, Any, List, Optional, Tuple

from horus.mock.twitter_data import create_mock_tweets

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
        from horus.twitter_monitor import TwitterSecurityMonitor
        
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
        logger.info(f"Starting Twitter monitoring (interval: {self.interval} seconds)...")
        logger.info("Using mock Twitter monitoring mode")
        
        def monitoring_loop():
            while not self.stop_event.is_set():
                try:
                    logger.info("Checking Twitter for security threats...")
                    security_alerts = self.twitter_monitor.check_for_security_threats()
                    
                    if security_alerts:
                        logger.info(f"Found {len(security_alerts)} potential security threats!")
                        
                        for alert in security_alerts:
                            logger.info("--------------------------------------------------")
                            logger.info("Processing security alert from Twitter:")
                            logger.info(f"Alert preview: {alert[:100]}")
                            if len(alert) > 100:
                                logger.info(f"        \n        ...")
                            
                            # Process the security alert
                            try:
                                response = self.security_agent.process_security_alert(alert)
                                logger.info(response)
                            except Exception as e:
                                logger.error(f"Error processing security alert: {str(e)}")
                            logger.info("--------------------------------------------------")
                    else:
                        logger.info("No security threats found.")
                    
                    # Sleep for the specified interval
                    for _ in range(self.interval):
                        if self.stop_event.is_set():
                            break
                        time.sleep(1)
                
                except Exception as e:
                    logger.error(f"Error in Twitter monitoring: {str(e)}")
                    # Sleep for a shorter interval before retrying
                    time.sleep(60)
        
        self.monitoring_thread = Thread(target=monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        return self.monitoring_thread
    
    def stop(self):
        """Stop the Twitter monitoring thread."""
        if self.monitoring_thread:
            logger.info("Stopping Twitter monitoring...")
            self.stop_event.set()
            self.monitoring_thread.join(timeout=5)
            logger.info("Twitter monitoring stopped.")
        
        return True
