#!/usr/bin/env python3
"""
Twitter Monitor Demo Script

This script demonstrates the Twitter monitoring functionality of the Horus security agent.
It fetches tweets from trusted security accounts, filters them for security relevance,
analyzes them with OpenAI, and formats security alerts.

Usage:
    python twitter_monitor_demo.py [--mock]

Options:
    --mock      Use mock data instead of making actual API calls
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

# Add the parent directory to the path so we can import the horus package
sys.path.append(str(Path(__file__).parent.parent))

# Set mock environment variables when running in mock mode
if '--mock' in sys.argv:
    # Set mock environment variables for testing
    os.environ["TWITTER_BEARER_TOKEN"] = "mock_bearer_token"
    os.environ["TWITTER_API_KEY"] = "mock_api_key"
    os.environ["TWITTER_API_SECRET"] = "mock_api_secret"
    os.environ["TWITTER_ACCESS_TOKEN"] = "mock_access_token"
    os.environ["TWITTER_ACCESS_TOKEN_SECRET"] = "mock_access_token_secret"
    os.environ["OPENAI_API_KEY"] = "mock_openai_key"

# Import the required modules
try:
    from dotenv import load_dotenv
    from openai import OpenAI
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please install the required dependencies using Poetry:")
    print("cd .. && poetry install")
    sys.exit(1)

# Load environment variables from .env file
load_dotenv()

class MockTweet:
    """Mock tweet object for demonstration purposes."""
    
    def __init__(self, id, text, created_at=None):
        self.id = id
        self.text = text
        self.created_at = created_at or datetime.now()


def create_mock_tweets():
    """Create mock tweets for demonstration purposes."""
    return [
        MockTweet(
            id=1,
            text="URGENT: We've discovered a critical vulnerability in the XYZ DeFi protocol that allows attackers to drain funds. All users should withdraw immediately!"
        ),
        MockTweet(
            id=2,
            text="New update released for our blockchain explorer. Check it out at example.com!"
        ),
        MockTweet(
            id=3,
            text="Security Alert: Phishing campaign targeting ABC Token holders. Fake airdrop site stealing private keys."
        ),
        MockTweet(
            id=4,
            text="We're excited to announce our new partnership with XYZ Protocol!"
        ),
        MockTweet(
            id=5,
            text="SECURITY BREACH: Multiple wallets compromised on DEX platform. Suspected smart contract exploit. Investigating."
        )
    ]


def create_mock_openai_response(tweet):
    """Create a mock OpenAI response for demonstration purposes."""
    # Only create security threat responses for tweets containing security keywords
    security_keywords = [
        "vulnerability", "exploit", "hack", "attack", "security", 
        "breach", "compromised", "scam", "phishing", "stolen",
        "drain", "urgent", "alert", "critical"
    ]
    
    is_security_threat = any(keyword.lower() in tweet.text.lower() for keyword in security_keywords)
    
    if is_security_threat:
        if "XYZ DeFi" in tweet.text:
            return {
                "is_security_threat": True,
                "threat_details": {
                    "summary": "Critical vulnerability in XYZ DeFi protocol allowing fund drainage",
                    "affected_systems": ["XYZ DeFi Protocol"],
                    "severity": "HIGH",
                    "urgency": "IMMEDIATE"
                }
            }
        elif "Phishing" in tweet.text:
            return {
                "is_security_threat": True,
                "threat_details": {
                    "summary": "Phishing campaign targeting ABC Token holders via fake airdrop site",
                    "affected_systems": ["ABC Token"],
                    "severity": "MEDIUM",
                    "urgency": "SOON"
                }
            }
        elif "SECURITY BREACH" in tweet.text:
            return {
                "is_security_threat": True,
                "threat_details": {
                    "summary": "Multiple wallets compromised on DEX platform due to smart contract exploit",
                    "affected_systems": ["DEX Platform"],
                    "severity": "HIGH",
                    "urgency": "IMMEDIATE"
                }
            }
    
    return {
        "is_security_threat": False
    }


def run_demo(use_mock=False):
    """Run the Twitter monitoring demo."""
    print("Starting Twitter Monitoring Demo")
    print("=" * 50)
    
    if use_mock:
        print("Using mock data for demonstration")
        
        # Create mock tweets
        tweets = create_mock_tweets()
        
        # Import the TwitterSecurityMonitor class
        try:
            from horus.twitter_monitor import TwitterSecurityMonitor
        except ImportError as e:
            print(f"Error importing TwitterSecurityMonitor: {e}")
            print("Please install the required dependencies using Poetry:")
            print("cd .. && poetry install")
            sys.exit(1)
            
        # Create a mock OpenAI client
        class MockOpenAI:
            def __init__(self, api_key=None):
                pass
            
            class chat:
                @staticmethod
                def completions():
                    pass
                
                class completions:
                    @staticmethod
                    def create(model=None, messages=None, response_format=None):
                        # Extract the tweet from the message
                        tweet_text = None
                        for message in messages:
                            if "Tweet: " in message["content"]:
                                lines = message["content"].split("\n")
                                for line in lines:
                                    if line.strip().startswith("Tweet: "):
                                        tweet_text = line.strip()[7:]  # Remove "Tweet: "
                        
                        # Find the corresponding mock tweet
                        mock_tweet = None
                        for tweet in tweets:
                            if tweet.text == tweet_text:
                                mock_tweet = tweet
                                break
                        
                        if not mock_tweet:
                            mock_tweet = MockTweet(0, tweet_text)
                        
                        # Create a mock response
                        mock_response = create_mock_openai_response(mock_tweet)
                        
                        # Create a mock choice
                        class MockChoice:
                            def __init__(self, content):
                                self.message = type('obj', (object,), {
                                    'content': json.dumps(content)
                                })
                        
                        # Create a mock response object
                        return type('obj', (object,), {
                            'choices': [MockChoice(mock_response)]
                        })
        
        # Initialize the monitor with the mock OpenAI client
        monitor = TwitterSecurityMonitor(openai_client=MockOpenAI())
        
        # Override the get_latest_tweets method to use mock data
        monitor.get_latest_tweets = lambda account_id, max_results=10: tweets
        
        # Run the monitoring process
        print("\nStep 1: Fetching tweets from trusted sources")
        print("-" * 50)
        for i, tweet in enumerate(tweets):
            print(f"Tweet {i+1}: {tweet.text}")
        
        print("\nStep 2: Filtering security-relevant tweets")
        print("-" * 50)
        relevant_tweets = monitor.filter_security_relevant_tweets(tweets)
        for i, tweet in enumerate(relevant_tweets):
            print(f"Relevant Tweet {i+1}: {tweet.text}")
        
        print("\nStep 3: Analyzing tweets for security threats")
        print("-" * 50)
        alerts = monitor.analyze_threads(relevant_tweets)
        
        print("\nStep 4: Formatted security alerts")
        print("-" * 50)
        if alerts:
            for i, alert in enumerate(alerts):
                print(f"Alert {i+1}:")
                print(alert)
                print()
        else:
            print("No security alerts generated.")
        
    else:
        # Check for required environment variables
        required_env_vars = [
            "TWITTER_BEARER_TOKEN", 
            "TWITTER_API_KEY", 
            "TWITTER_API_SECRET", 
            "TWITTER_ACCESS_TOKEN", 
            "TWITTER_ACCESS_TOKEN_SECRET",
            "OPENAI_API_KEY"
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        
        if missing_vars:
            print(f"Missing required environment variables: {', '.join(missing_vars)}")
            print("Please set these variables in a .env file or in your environment.")
            print("For demonstration purposes, you can use the --mock flag to run with mock data:")
            print("python examples/twitter_monitor_demo.py --mock")
            return
        
        try:
            # Import the TwitterSecurityMonitor class
            try:
                from horus.twitter_monitor import TwitterSecurityMonitor
            except ImportError as e:
                print(f"Error importing TwitterSecurityMonitor: {e}")
                print("Please install the required dependencies using Poetry:")
                print("cd .. && poetry install")
                sys.exit(1)
            
            # Initialize OpenAI client
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Initialize the monitor
            monitor = TwitterSecurityMonitor(openai_client=openai_client)
            
            # Override the trusted sources with real security accounts
            monitor.trusted_sources = [
                "1394563210",  # Example: CertiK
                "4334324345",  # Example: PeckShield
                "2349102345"   # Example: SlowMist
            ]
            
            print("\nStep 1: Fetching tweets from trusted sources")
            print("-" * 50)
            all_tweets = []
            for source_id in monitor.trusted_sources:
                print(f"Fetching tweets from account {source_id}...")
                tweets = monitor.get_latest_tweets(source_id)
                all_tweets.extend(tweets)
                print(f"Found {len(tweets)} tweets.")
            
            if not all_tweets:
                print("No tweets found from trusted sources.")
                return
            
            print("\nStep 2: Filtering security-relevant tweets")
            print("-" * 50)
            relevant_tweets = monitor.filter_security_relevant_tweets(all_tweets)
            print(f"Found {len(relevant_tweets)} security-relevant tweets out of {len(all_tweets)} total tweets.")
            
            for i, tweet in enumerate(relevant_tweets):
                print(f"Relevant Tweet {i+1}: {tweet.text[:100]}...")
            
            print("\nStep 3: Analyzing tweets for security threats")
            print("-" * 50)
            print(f"Analyzing {len(relevant_tweets)} tweets with OpenAI...")
            alerts = monitor.analyze_threads(relevant_tweets)
            
            print("\nStep 4: Formatted security alerts")
            print("-" * 50)
            if alerts:
                print(f"Generated {len(alerts)} security alerts.")
                for i, alert in enumerate(alerts):
                    print(f"Alert {i+1}:")
                    print(alert)
                    print()
            else:
                print("No security alerts generated.")
            
        except Exception as e:
            print(f"Error running Twitter monitoring: {e}")
            print("For demonstration purposes, you can use the --mock flag to run with mock data:")
            print("python examples/twitter_monitor_demo.py --mock")
            return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Twitter Monitor Demo Script")
    parser.add_argument("--mock", action="store_true", help="Use mock data instead of making actual API calls")
    
    args = parser.parse_args()
    
    run_demo(use_mock=args.mock)
