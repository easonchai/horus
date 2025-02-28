#!/usr/bin/env python3
"""
Twitter Monitor Demo Script

This script demonstrates the Twitter monitoring functionality of the Horus security agent.
It fetches tweets from trusted security accounts, filters them for security relevance,
analyzes them with OpenAI, and formats security alerts.

Usage:
    python twitter_monitor_demo.py

No options needed as it now uses mock data by default.
"""

import os
import sys
import json
from pathlib import Path

# Add the parent directory to the path so we can import the horus package
sys.path.append(str(Path(__file__).parent.parent))

# Import from our new modular structure
from horus.mock.twitter_data import MockTweet, create_mock_tweets, create_mock_openai_response
from horus.mock.openai_client import MockOpenAI
from horus.agents.security_agent import SecurityAgent
from horus.agents.twitter_agent import TwitterAgent

def run_demo():
    """Run the Twitter monitoring demo."""
    print("Starting Twitter monitoring demo...")
    
    # Create a security agent with a mock OpenAI client
    mock_client = MockOpenAI()
    security_agent = SecurityAgent(mock_client)
    
    # Create and start the Twitter agent
    twitter_agent = TwitterAgent(security_agent, interval=10)
    twitter_thread = twitter_agent.start()
    
    try:
        print("Twitter monitoring started. Press Ctrl+C to stop.")
        # Keep the main thread alive
        while True:
            # This allows for Ctrl+C to work properly
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping Twitter monitoring...")
    finally:
        # Stop the Twitter agent
        twitter_agent.stop()
        print("Twitter monitoring stopped.")

if __name__ == "__main__":
    run_demo()
