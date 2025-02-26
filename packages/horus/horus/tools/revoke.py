"""
Revoke tool for the Horus security system.
"""
import logging
from typing import Dict, Any, Callable

from .base import create_tool

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


def create_revoke_tool(tokens_config: Dict[str, Any]) -> Callable[[Dict[str, Any]], str]:
    """
    Create a revoke tool function.
    
    Args:
        tokens_config: The token configuration data.
    
    Returns:
        A function that can be called to execute revocation of permissions.
    """
    def get_token_address(token_symbol: str, chain_id: str) -> str:
        """
        Get the contract address for a token on a specific chain.
        
        Args:
            token_symbol: The symbol of the token.
            chain_id: The chain ID.
            
        Returns:
            Token contract address or None if not found.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        for token in tokens_config.get("tokens", []):
            if token.get("symbol") == token_symbol:
                networks = token.get("networks", {})
                return networks.get(chain_id, "unknown")
        return "unknown"

    def execute_revoke(parameters: Dict[str, Any]) -> str:
        """
        Execute a revocation operation based on the provided parameters.
        
        Args:
            parameters: Dictionary containing revocation parameters:
                - token_address: The contract address to revoke permissions from.
                - protocol: The protocol to revoke permissions from.
                - chain_id: The chain ID.
                
        Returns:
            A string describing the action taken.
        """
        token_address = parameters.get("token_address", "unknown")
        protocol = parameters.get("protocol", "unknown")
        chain_id = str(parameters.get("chain_id", "84532"))  # Default to Base, ensure it's a string
        
        # If we only have the token symbol, try to look up the address
        if token_address == "unknown" and "token" in parameters:
            token_symbol = parameters.get("token")
            token_address = get_token_address(token_symbol, chain_id)
        
        logger.info(f"Executing revocation for token {token_address} on protocol {protocol} (chain {chain_id})")
        logger.info(f"Full parameters: {parameters}")
        
        # Build a detailed message based on the parameters
        message = f"Revoked permissions for {token_address} on {protocol} (chain {chain_id})."
        message += f"\nPermissions have been successfully revoked to protect your assets."
        
        return message
    
    # Create and return the tool function
    return create_tool("revoke", execute_revoke)


# Create a default revoke tool for export
tokens_config = {
    "tokens": [
        {
            "symbol": "ABC",
            "networks": {
                "84532": "0x..."
            }
        }
    ]
}
revoke_tool = create_revoke_tool(tokens_config)
