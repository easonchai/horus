"""
Mock OpenAI client for testing the Horus security monitoring agent.
"""
import json
from typing import List, Dict, Any, Optional

from .twitter_data import MockTweet, create_mock_tweets


class MockOpenAI:
    """Mock OpenAI client for testing."""
    
    def __init__(self, api_key=None):
        """Initialize the mock OpenAI client."""
        self.mock_tweets = create_mock_tweets()
        
    class chat:
        """Mock OpenAI chat completions API."""
        
        class completions:
            """Mock OpenAI chat completions API."""
            
            @staticmethod
            def create(model=None, messages=None, response_format=None):
                """Create a mock chat completion."""
                # Extract the tweet or security alert from the message
                tweet_text = ""
                for message in messages:
                    if "Tweet: " in message["content"]:
                        lines = message["content"].split("\n")
                        for line in lines:
                            if line.strip().startswith("Tweet: "):
                                tweet_text = line.strip()[7:]  # Remove "Tweet: "
                    elif message["role"] == "user":
                        tweet_text = message["content"]
                
                # Check if this is a security alert analysis request
                is_alert_analysis = False
                for message in messages:
                    if message["role"] == "system" and "You are Horus, a security monitoring agent" in message["content"]:
                        is_alert_analysis = True
                        break
                
                if is_alert_analysis:
                    return MockOpenAI._create_security_alert_response(tweet_text)
                else:
                    return MockOpenAI._create_tweet_analysis_response(tweet_text)
    
    @staticmethod
    def _create_security_alert_response(tweet_text: str):
        """Create a mock response for security alert analysis."""
        if "XYZ DeFi" in tweet_text or "critical vulnerability" in tweet_text.lower():
            mock_response = {
                "reasoning": "The alert indicates a critical vulnerability in the XYZ DeFi protocol that allows funds to be drained. To protect the user's funds, we must immediately withdraw any assets held in the XYZ DeFi protocol to a secure address.",
                "action_plan": [
                    {
                        "action": "withdrawal",
                        "explanation": "Withdraw all assets from the compromised XYZ DeFi protocol to prevent loss due to the vulnerability that allows attackers to drain funds.",
                        "parameters": {
                            "token": "all",
                            "amount": "all",
                            "destination": "safe_address_here"
                        }
                    }
                ]
            }
        elif "Phishing" in tweet_text or "ABC Token" in tweet_text:
            mock_response = {
                "reasoning": "The security alert indicates a phishing campaign targeting holders of the ABC Token. We should revoke permissions to protect user funds.",
                "action_plan": [
                    {
                        "action": "revoke",
                        "explanation": "To protect users from unauthorized transactions initiated by attackers using stolen private keys, revoke current permissions to the ABC Token.",
                        "parameters": {
                            "token_address": "ADDRESS_OF_ABC_TOKEN",
                            "protocol": "ProtocolUsingABC"
                        }
                    }
                ]
            }
        elif "SECURITY BREACH" in tweet_text or "wallets compromised" in tweet_text.lower() or "DEX platform" in tweet_text:
            mock_response = {
                "reasoning": "Multiple wallets have been compromised on the DEX platform due to a smart contract exploit. We need to take immediate action to protect user funds.",
                "action_plan": [
                    {
                        "action": "withdrawal",
                        "explanation": "Withdraw funds from the compromised DEX platform to prevent loss.",
                        "parameters": {
                            "token": "all",
                            "amount": "all",
                            "destination": "safe_wallet_address"
                        }
                    }
                ]
            }
        else:
            mock_response = {
                "reasoning": "This alert doesn't require immediate action.",
                "action_plan": []
            }
        
        # Create a mock choice with the JSON response as a string
        class MockChoice:
            def __init__(self, content):
                self.message = type('obj', (object,), {
                    'content': content
                })
        
        return type('obj', (object,), {
            'choices': [MockChoice(json.dumps(mock_response))]
        })
    
    @staticmethod
    def _create_tweet_analysis_response(tweet_text: str):
        """Create a mock response for tweet analysis."""
        # Find the corresponding mock tweet
        mock_tweets = create_mock_tweets()
        mock_tweet = None
        for tweet in mock_tweets:
            if tweet.text == tweet_text:
                mock_tweet = tweet
                break
        
        if not mock_tweet:
            mock_tweet = MockTweet(0, tweet_text)
        
        # Create a mock response based on the tweet content
        if "SECURITY ALERT" not in tweet_text:
            mock_response = {
                "is_security_threat": False,
                "explanation": "This tweet does not contain a security alert."
            }
        else:
            mock_response = {
                "is_security_threat": True,
                "explanation": f"This tweet contains a security alert: {tweet_text}",
                "severity": "high" if "critical" in tweet_text.lower() or "breach" in tweet_text.lower() else "medium",
                "affected_assets": ["XYZ_TOKEN"] if "XYZ" in tweet_text else ["ABC_TOKEN"] if "ABC" in tweet_text else ["UNKNOWN"],
                "recommended_action": "withdrawal" if "vulnerability" in tweet_text.lower() or "breach" in tweet_text.lower() else "revoke" if "phishing" in tweet_text.lower() else "monitor"
            }
        
        class MockChoice:
            def __init__(self, content):
                self.message = type('obj', (object,), {
                    'content': content
                })
        
        return type('obj', (object,), {
            'choices': [MockChoice(json.dumps(mock_response))]
        })
