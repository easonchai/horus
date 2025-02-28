"""
Mock Twitter data for testing the Horus security monitoring agent.
"""
import json
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class MockTweet:
    """Mock tweet object for testing."""
    id: int
    text: str
    author_id: str = "12345"
    created_at: str = "2025-02-25T12:00:00Z"


def create_mock_tweets() -> List[MockTweet]:
    """Create a list of mock tweets for testing."""
    return [
        MockTweet(1, "SECURITY ALERT: Critical vulnerability in XYZ DeFi protocol allowing fund drainage"),
        MockTweet(2, "SECURITY ALERT: Phishing campaign targeting ABC Token holders via fake airdrop site"),
        MockTweet(3, "SECURITY ALERT: SECURITY BREACH: Multiple wallets compromised on DEX platform"),
        MockTweet(4, "Just released a new security tool for smart contract auditing"),
        MockTweet(5, "Reminder: Always use hardware wallets for cold storage"),
        MockTweet(6, "SECURITY ALERT: New malware targeting crypto wallets detected"),
        MockTweet(7, "SECURITY ALERT: Suspicious activity detected on DEF exchange"),
        MockTweet(8, "SECURITY ALERT: Potential front-running vulnerability in GHI protocol"),
        MockTweet(9, "SECURITY ALERT: Zero-day exploit found in popular wallet extension"),
    ]


def create_mock_openai_response(tweet: MockTweet) -> Dict[str, Any]:
    """Create a mock OpenAI response for a tweet."""
    if "SECURITY ALERT" not in tweet.text:
        return {
            "is_security_threat": False,
            "explanation": "This tweet does not contain a security alert."
        }
    
    return {
        "is_security_threat": True,
        "explanation": f"This tweet contains a security alert: {tweet.text}",
        "severity": "high" if "critical" in tweet.text.lower() or "breach" in tweet.text.lower() else "medium",
        "affected_assets": ["XYZ_TOKEN"] if "XYZ" in tweet.text else ["ABC_TOKEN"] if "ABC" in tweet.text else ["UNKNOWN"],
        "recommended_action": "withdrawal" if "vulnerability" in tweet.text.lower() or "breach" in tweet.text.lower() else "revoke" if "phishing" in tweet.text.lower() else "monitor"
    }
