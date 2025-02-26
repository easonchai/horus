"""
Revoke tool for the Horus security system.
"""
import logging
from typing import Dict, Any

from .base import BaseTool

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


class RevokeTool(BaseTool):
    """Tool for revoking permissions from protocols."""
    
    def __init__(self, tokens_config: Dict[str, Any]):
        """
        Initialize the revoke tool.
        
        Args:
            tokens_config: The token configuration data.
        """
        self.tokens_config = tokens_config
    
    def get_token_address(self, token_symbol: str, chain_id: str) -> str:
        """
        Get the contract address for a token on a specific chain.
        
        Args:
            token_symbol: The symbol of the token.
            chain_id: The chain ID.
            
        Returns:
            Token contract address or None if not found.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        for token in self.tokens_config.get("tokens", []):
            if token.get("symbol") == token_symbol:
                networks = token.get("networks", {})
                return networks.get(chain_id, "unknown")
        return "unknown"
    
    def execute(self, parameters: Dict[str, Any]) -> str:
        """
        Execute a revoke operation based on the provided parameters.
        
        Args:
            parameters: Dictionary containing revoke parameters:
                - token_address: The contract address to revoke permissions from.
                - protocol: The protocol to revoke permissions from.
                - chain_id: The chain ID.
                
        Returns:
            A string describing the action taken.
        """
        token_address = parameters.get("token_address", "unknown")
        protocol = parameters.get("protocol", "unknown")
        chain_id = str(parameters.get("chain_id", "84532"))
        
        # If we only have the token symbol, try to look up the address
        if token_address == "unknown" and "token" in parameters:
            token_symbol = parameters.get("token")
            token_address = self.get_token_address(token_symbol, chain_id)
        
        logger.info(f"REVOKE TOOL CALLED: Revoking permissions for {token_address} on {protocol}")
        
        # In a real implementation, this would call the blockchain to revoke permissions
        return f"Permissions revoked for {token_address} on {protocol}."
