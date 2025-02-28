"""
Example usage of the revoke tool with AgentKit.

This example demonstrates how to use the revoke tool to revoke token approvals
using Coinbase's AgentKit.

Prerequisites:
- CDP_API_KEY_NAME and CDP_API_KEY_PRIVATE_KEY environment variables must be set
- coinbase-agentkit and coinbase-agentkit-langchain must be installed
"""
import os
import logging
from dotenv import load_dotenv

from agents.security_agent import SecurityAgent
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    """
    Main function to demonstrate the revoke tool.
    """
    # Check for required environment variables
    required_vars = ["OPENAI_API_KEY", "CDP_API_KEY_NAME", "CDP_API_KEY_PRIVATE_KEY"]
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please set these variables in a .env file or in your environment.")
        return
    
    # Initialize OpenAI client
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    
    # Create security agent
    agent = SecurityAgent(openai_client, mock_openai=False, mock_twitter=True)
    
    # Example security alert for token approval revocation
    alert_text = """
    SECURITY ALERT: Suspicious approval detected for USDC token to spender 0x1234567890123456789012345678901234567890 
    on Base Sepolia (chain_id: 84532). This approval was made to a protocol that has been flagged for potential 
    security issues. Consider revoking this approval immediately.
    """
    
    # Process the alert
    logger.info("Processing security alert...")
    response = agent.process_security_alert(alert_text)
    
    # Log the response
    logger.info(f"Agent response: {response}")

if __name__ == "__main__":
    main()
