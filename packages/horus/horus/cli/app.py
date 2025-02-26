"""
Command-line interface for the Horus security monitoring agent.
"""
import argparse
import logging
import sys
import os
from typing import Dict, Any, Optional

from openai import OpenAI
from dotenv import load_dotenv

from horus.agents.security_agent import SecurityAgent
from horus.agents.twitter_agent import TwitterAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


class HorusApp:
    """Command-line interface for the Horus security monitoring agent."""
    
    def __init__(self):
        """Initialize the Horus app."""
        # Load environment variables
        load_dotenv()
        
        # Use real OpenAI client
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.security_agent = SecurityAgent(self.openai_client)
        self.twitter_agent = None
    
    def parse_args(self):
        """Parse command-line arguments."""
        parser = argparse.ArgumentParser(description="Horus - Crypto Security Monitoring Agent")
        parser.add_argument("--interval", type=int, default=300, help="Twitter monitoring interval in seconds")
        parser.add_argument("--test", action="store_true", help="Run the test scenario")
        
        return parser.parse_args()
    
    def start(self):
        """Start the Horus app."""
        args = self.parse_args()
        
        logger.info("Starting Horus Security Monitoring Agent...")
        
        # Start Twitter monitoring
        self.twitter_agent = TwitterAgent(self.security_agent, interval=args.interval)
        self.twitter_agent.start()
        
        # Run test scenario if requested
        if args.test:
            self.run_test_scenario()
            return
        
        # Start interactive mode
        try:
            logger.info("\nEnter a security alert message (or type 'exit' to quit):")
            while True:
                try:
                    user_input = input("> ")
                    if user_input.lower() == "exit":
                        break
                    
                    if user_input.strip():
                        response = self.security_agent.process_security_alert(user_input)
                        logger.info(response)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.error(f"Error: {str(e)}")
        
        finally:
            # Stop Twitter monitoring
            if self.twitter_agent:
                self.twitter_agent.stop()
    
    def run_test_scenario(self):
        """Run a test scenario with predefined security alerts."""
        logger.info("Running test scenario...")
        
        test_alerts = [
            "SECURITY ALERT: Critical vulnerability in XYZ DeFi protocol allowing fund drainage",
            "SECURITY ALERT: Phishing campaign targeting ABC Token holders via fake airdrop site",
            "SECURITY ALERT: SECURITY BREACH: Multiple wallets compromised on DEX platform",
        ]
        
        for alert in test_alerts:
            logger.info("--------------------------------------------------")
            logger.info(f"Processing test alert: {alert}")
            response = self.security_agent.process_security_alert(alert)
            logger.info(response)
            logger.info("--------------------------------------------------")
        
        logger.info("Test scenario completed.")


def main():
    """Main entry point for the Horus app."""
    app = HorusApp()
    app.start()


if __name__ == "__main__":
    main()
