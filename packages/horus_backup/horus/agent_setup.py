"""
Agent setup functionality for the Horus security monitoring agent.

This module provides functions to set up the Horus agent with the necessary components.
"""
import logging
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from horus.core.agent_kit import agent_kit_manager
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def setup_agent() -> Optional[Dict[str, Any]]:
    """
    Set up the Horus security monitoring agent with necessary components.
    
    This function initializes components needed for the Horus agent, including
    the OpenAI client and AgentKit components via the centralized agent_kit_manager.
    
    Returns:
        Dict containing the initialized components or None if setup failed
    """
    # Check for OpenAI API key
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        logger.error("Missing OPENAI_API_KEY in environment variables")
        logger.warning("Please set OPENAI_API_KEY in a .env file or in your environment")
        return None
    
    try:
        # Initialize OpenAI client
        openai_client = OpenAI(api_key=openai_api_key)
        
        # Initialize AgentKit using the centralized manager
        logger.info("Initializing Coinbase AgentKit via agent_kit_manager...")
        agentkit_components = agent_kit_manager.initialize_agentkit()
        
        # Return all components needed by the application
        return {
            "agent_kit": agentkit_components.get("agentkit"),
            "wallet_provider": agentkit_components.get("wallet_provider"),
            "action_provider": agentkit_components.get("action_provider"),
            "wallet_address": agentkit_components.get("wallet_address"),
            "openai_client": openai_client
        }
    except Exception as e:
        logger.error(f"Error setting up agent: {str(e)}")
        return None 