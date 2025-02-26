#!/usr/bin/env python3
"""
Test script for the Security Agent.
"""
import json
import logging
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the security agent
from horus.agents.security_agent import SecurityAgent


def test_security_alert():
    """
    Test the security agent's ability to process security alerts.
    """
    # Initialize OpenAI client
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create security agent with mock OpenAI to avoid API calls during testing
    security_agent = SecurityAgent(openai_client, mock_openai=True)
    
    # Process a test alert
    test_alert = """
    CRITICAL SECURITY ALERT: Beefy protocol vulnerability detected on Base!
    
    A critical vulnerability has been identified in the Beefy protocol's vault contracts
    on the Base chain. This vulnerability could allow an attacker to drain funds from affected vaults.
    
    Affected users: All users with beefyUSDC-USDT positions on Base
    Risk level: HIGH
    Recommendation: Withdraw funds immediately
    """
    
    print("\nContext Being Provided to LLM:")
    print("=" * 80)
    print(security_agent._prepare_context_for_ai())
    print("=" * 80)
    
    print("\nSecurity Alert Processing Result:")
    print("-" * 50)
    result = security_agent.process_security_alert(test_alert)
    print(result)
    print("-" * 50)


def test_revoke_tool():
    """
    Test the revoke tool directly.
    """
    # Initialize OpenAI client
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create security agent
    security_agent = SecurityAgent(openai_client)
    
    # Test parameters
    parameters = {
        "token": "USDC", 
        "protocol": "Compromised Protocol",
        "chain_id": "84532"
    }
    
    # Execute the revoke tool
    print("\nRevoke Tool Test:")
    print("-" * 50)
    result = security_agent.revoke_tool(parameters)
    print(result)
    print("-" * 50)


def test_monitor_tool():
    """
    Test the monitor tool directly.
    """
    # Initialize OpenAI client
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    # Create security agent
    security_agent = SecurityAgent(openai_client)
    
    # Test parameters
    parameters = {
        "asset": "All Base Chain Positions", 
        "duration": "48h"
    }
    
    # Execute the monitor tool
    print("\nMonitor Tool Test:")
    print("-" * 50)
    result = security_agent.monitor_tool(parameters)
    print(result)
    print("-" * 50)


# Run the test
if __name__ == "__main__":
    test_security_alert()
    test_revoke_tool()
    test_monitor_tool()
