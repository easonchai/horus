"""
Command-line interface for the Horus security monitoring agent.
"""
import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from agents.security_agent import SecurityAgent
from agents.twitter_agent import TwitterAgent
from core.agent_kit import agent_kit_manager
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


class HorusApp:
    """Command-line interface for the Horus security monitoring agent."""
    
    def __init__(self):
        """Initialize the Horus app."""
        # Load environment variables
        load_dotenv()
        
        # Check for OpenAI API key
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            logger.error("Missing OPENAI_API_KEY in environment variables")
            logger.warning("Please set OPENAI_API_KEY in your .env file or environment variables")
        
        # Initialize OpenAI client
        self.openai_client = OpenAI(api_key=openai_api_key)
        
        # Initialize AgentKit using the simplified manager
        logger.info("Initializing Coinbase AgentKit...")
        try:
            agentkit_components = agent_kit_manager.initialize_agentkit()
            
            # Log wallet status
            if agentkit_components["wallet_address"]:
                wallet_address = agentkit_components["wallet_address"]
                logger.info(f"Wallet initialized with address: {wallet_address[:6]}...{wallet_address[-4:]}")
            else:
                logger.warning("No wallet initialized. Blockchain operations will be limited to simulation mode.")
                
        except Exception as e:
            logger.error(f"Failed to initialize AgentKit: {str(e)}")
            logger.warning("Blockchain operations will be limited to simulation mode")
            agentkit_components = {
                "wallet_provider": None,
                "action_provider": None,
                "wallet_address": None,
                "agentkit": None
            }
        
        # Initialize security agent with both OpenAI client and AgentKit
        self.security_agent = SecurityAgent(
            openai_client=self.openai_client,
            agent_kit_manager=agent_kit_manager
        )
        
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
        
        # Display a welcome banner
        self._display_welcome_banner()
        
        # Show configuration
        print("\033[1;33m[CONFIG]\033[0m OpenAI API Key Status:", "\033[1;32mConfigured ✓\033[0m" if os.getenv("OPENAI_API_KEY") else "\033[1;31mMissing ✗\033[0m")
        print("\033[1;33m[CONFIG]\033[0m Twitter API Status:", "\033[1;35mUsing Mocks\033[0m")
        print("\033[1;33m[CONFIG]\033[0m CDP API Status:", "\033[1;35mUsing Mocks\033[0m")
        print("\033[1;33m[CONFIG]\033[0m Monitoring Interval:", f"\033[1;36m{args.interval} seconds\033[0m")
        print("\033[1;33m[CONFIG]\033[0m Demo Mode:", "\033[1;32mEnabled ✓\033[0m" if args.test else "\033[1;33mDisabled ✗\033[0m")
        print("-" * 80)
        
        # Start Twitter monitoring with shorter interval in demo mode
        if args.test:
            print("\033[1;36m[DEMO]\033[0m Starting demo mode with shorter monitoring interval (30 seconds)")
            self.twitter_agent = TwitterAgent(self.security_agent, interval=30)
        else:
            print(f"\033[1;34m[INFO]\033[0m Starting Twitter monitoring with interval of {args.interval} seconds")
            self.twitter_agent = TwitterAgent(self.security_agent, interval=args.interval)
            
        self.twitter_agent.start()
        
        # Run the test scenario in test mode
        if args.test:
            print("\033[1;36m[DEMO]\033[0m Running test scenario with simulated security alerts")
            self.run_test_scenario()
        else:
            print("\033[1;34m[INFO]\033[0m Monitoring active. Press Ctrl+C to stop.")
            try:
                # Keep the main thread running
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\033[1;33m[SHUTDOWN]\033[0m Keyboard interrupt received, shutting down...")
                self.stop()
    
    def _display_welcome_banner(self):
        """Display a welcome banner for the Horus Security Agent."""
        banner = """
\033[1;36m██╗  ██╗ ██████╗ ██████╗ ██╗   ██╗███████╗\033[0m
\033[1;36m██║  ██║██╔═══██╗██╔══██╗██║   ██║██╔════╝\033[0m
\033[1;36m███████║██║   ██║██████╔╝██║   ██║███████╗\033[0m
\033[1;36m██╔══██║██║   ██║██╔══██╗██║   ██║╚════██║\033[0m
\033[1;36m██║  ██║╚██████╔╝██║  ██║╚██████╔╝███████║\033[0m
\033[1;36m╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝\033[0m
                                     
\033[1;33m      Crypto Security Monitoring Agent\033[0m
\033[0;37m         ETHDenver 2025 Hackathon\033[0m
        """
        print(banner)
        print("=" * 80)
        print("\033[1;32m🔒 SYSTEM STARTUP\033[0m")
        print("=" * 80)
    
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
    
    def stop(self):
        """Stop the Horus app."""
        if self.twitter_agent:
            self.twitter_agent.stop()


def main():
    """Main entry point for the Horus app."""
    app = HorusApp()
    app.start()


if __name__ == "__main__":
    main()
