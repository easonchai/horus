"""
Monitor tool for the Horus security system.

This module provides functionality for monitoring assets and configuring enhanced 
security measures during suspicious activity.
"""
import logging
from typing import Any, Callable, Dict, List, Optional

from .base import BaseTool, create_tool
from .constants import DEFAULT_CHAIN_ID

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


class MonitorTool(BaseTool):
    """
    Tool for configuring enhanced monitoring of assets during suspicious activity.
    
    This tool allows for:
    1. Setting up enhanced monitoring for specific assets
    2. Configuring alert thresholds
    3. Customizing monitoring duration
    4. Enabling additional security checks for specific tokens or protocols
    
    Attributes:
        alert_subscribers (List[str]): List of addresses or services to notify of alerts
        active_monitors (Dict[str, Dict[str, Any]]): Dictionary tracking active monitoring configurations
    """
    
    def __init__(self, alert_subscribers: List[str] = None):
        """
        Initialize the monitoring tool with configuration.
        
        Args:
            alert_subscribers: Optional list of addresses or services to notify of alerts
        """
        super().__init__("monitor")
        self.alert_subscribers = alert_subscribers or []
        self.active_monitors = {}
        
        logger.info("MonitorTool initialized with %d alert subscribers", len(self.alert_subscribers))
    
    def add_subscriber(self, subscriber: str) -> None:
        """
        Add a subscriber to receive monitoring alerts.
        
        Args:
            subscriber: Address or service identifier to receive alerts
        """
        if subscriber not in self.alert_subscribers:
            self.alert_subscribers.append(subscriber)
            logger.info("Added alert subscriber: %s", subscriber)
    
    def remove_subscriber(self, subscriber: str) -> None:
        """
        Remove a subscriber from the alert list.
        
        Args:
            subscriber: Address or service identifier to remove
        """
        if subscriber in self.alert_subscribers:
            self.alert_subscribers.remove(subscriber)
            logger.info("Removed alert subscriber: %s", subscriber)
    
    def get_active_monitors(self, chain_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Get all active monitoring configurations, optionally filtered by chain.
        
        Args:
            chain_id: Optional chain ID to filter results
            
        Returns:
            Dictionary of active monitoring configurations
        """
        if chain_id:
            return {k: v for k, v in self.active_monitors.items() if v.get("chain_id") == chain_id}
        return self.active_monitors
    
    def execute(self, parameters: Dict[str, Any]) -> str:
        """
        Execute a monitoring operation based on the provided parameters.
        
        Args:
            parameters: Dictionary containing monitoring parameters:
                - asset: The asset to monitor (token symbol, protocol name, or "ALL")
                - duration: The duration to monitor for (e.g., "24h", "7d")
                - threshold: The threshold for alerts (e.g., "5%", "10%")
                - chain_id: The chain ID to monitor (optional)
                - alert_type: Type of alerts to enable (optional, e.g., "price", "volume", "txs")
                - notify: Additional subscribers to notify (optional)
                
        Returns:
            A string describing the action taken.
        """
        asset = parameters.get("asset", "unknown")
        duration = parameters.get("duration", "24h")
        threshold = parameters.get("threshold", "5%")
        chain_id = str(parameters.get("chain_id", DEFAULT_CHAIN_ID))
        alert_type = parameters.get("alert_type", "price")
        additional_subscribers = parameters.get("notify", [])
        
        logger.info("Executing monitoring for asset %s for duration %s", asset, duration)
        logger.info("Full parameters: %s", parameters)
        
        # Add any additional subscribers
        for subscriber in additional_subscribers:
            self.add_subscriber(subscriber)
        
        # Create a monitoring configuration
        monitor_config = {
            "asset": asset,
            "duration": duration,
            "threshold": threshold,
            "chain_id": chain_id,
            "alert_type": alert_type,
            "active": True,
            "subscribers": self.alert_subscribers.copy(),
        }
        
        # Add to active monitors
        monitor_key = f"{asset}:{chain_id}"
        self.active_monitors[monitor_key] = monitor_config
        
        # Build a detailed message based on the parameters
        message = f"Enhanced monitoring activated for {asset} for the next {duration}."
        message += f"\nYou will be alerted of any {alert_type} movements exceeding {threshold}."
        
        if len(self.alert_subscribers) > 0:
            message += f"\nAlerts will be sent to {len(self.alert_subscribers)} configured recipients."
        
        message += f"\nAdditional security checks have been enabled for this asset on chain {chain_id}."
        
        return message


# Factory function to create a monitor tool
def create_monitor_tool(alert_subscribers: List[str] = None) -> MonitorTool:
    """
    Create a monitor tool.
    
    Args:
        alert_subscribers: Optional list of addresses or services to notify of alerts
        
    Returns:
        A MonitorTool instance that can be called to execute monitoring operations.
        
    Example:
        ```python
        # Create a monitor tool with alert subscribers
        monitor_tool = create_monitor_tool(["0x1234...", "email@example.com"])
        
        # Execute a monitoring operation
        result = monitor_tool({
            "asset": "ETH",
            "duration": "24h",
            "threshold": "5%"
        })
        ```
    """
    return MonitorTool(alert_subscribers)


# Create a default monitor tool for export
monitor_tool = create_monitor_tool()
