"""
Agent setup functionality for the Horus security monitoring agent.

This module provides functions to set up the Horus agent with the necessary components.
"""
import logging
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def setup_agent() -> Optional[Dict[str, Any]]:
    """
    Set up the Horus security monitoring agent with necessary components.
    
    This function checks for required environment variables and initializes
    the OpenAI client and Agent components.
    
    Returns:
        Dict containing the initialized components or None if setup failed
    """
    # Check for required environment variables
    required_env_vars = ["CDP_API_KEY_NAME", "CDP_API_KEY_PRIVATE_KEY", "OPENAI_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in a .env file or in your environment.")
        return None
    
    try:
        # Import Coinbase Agent Kit if available
        try:
            from coinbase_agentkit import AgentKit
            agent_kit = AgentKit()
        except ImportError:
            logger.warning("Coinbase AgentKit not available, some features will be limited")
            agent_kit = None
        
        # Initialize OpenAI client
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        return {
            "agent_kit": agent_kit,
            "openai_client": openai_client
        }
    except Exception as e:
        print(f"Error setting up agent: {str(e)}")
        return None 