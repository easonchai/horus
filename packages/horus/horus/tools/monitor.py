"""
Monitor tool for the Horus security system.
"""
import logging
from typing import Dict, Any, Callable

from .base import create_tool

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


def create_monitor_tool() -> Callable[[Dict[str, Any]], str]:
    """
    Create a monitor tool function.
    
    Returns:
        A function that can be called to execute monitoring operations.
    """
    def execute_monitor(parameters: Dict[str, Any]) -> str:
        """
        Execute a monitoring operation based on the provided parameters.
        
        Args:
            parameters: Dictionary containing monitoring parameters:
                - asset: The asset to monitor.
                - duration: The duration to monitor for.
                - threshold: The threshold for alerts.
                
        Returns:
            A string describing the action taken.
        """
        asset = parameters.get("asset", "unknown")
        duration = parameters.get("duration", "24h")
        threshold = parameters.get("threshold", "5%")
        
        logger.info(f"Executing monitoring for asset {asset} for duration {duration}")
        logger.info(f"Full parameters: {parameters}")
        
        # Build a detailed message based on the parameters
        message = f"Enhanced monitoring activated for {asset} for the next {duration}."
        message += f"\nYou will be alerted of any price movements exceeding {threshold}."
        message += f"\nAdditional security checks have been enabled for this asset."
        
        return message
    
    # Create and return the tool function
    return create_tool("monitor", execute_monitor)


# Create a default monitor tool for export
monitor_tool = create_monitor_tool()
