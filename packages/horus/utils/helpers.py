"""
Helper functions for the Horus security monitoring agent.
"""
import json
import logging
import os
from typing import Dict, Any, List, Optional, Union

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


def load_env_vars(env_file: str = ".env") -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_file: Path to the .env file.
        
    Returns:
        A dictionary of environment variables.
    """
    env_vars = {}
    
    try:
        if os.path.exists(env_file):
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        env_vars[key] = value
                        os.environ[key] = value
    except Exception as e:
        logger.error(f"Error loading environment variables: {str(e)}")
    
    return env_vars


def safe_json_loads(json_str: str) -> Dict[str, Any]:
    """
    Safely load a JSON string.
    
    Args:
        json_str: JSON string to load.
        
    Returns:
        A dictionary of the parsed JSON.
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {str(e)}")
        logger.debug(f"JSON string: {json_str}")
        return {}
