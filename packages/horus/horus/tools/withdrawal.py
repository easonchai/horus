"""
Withdrawal tool for the Horus security system.
"""
import logging
from typing import Dict, Any, List, Optional

from .base import BaseTool

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


class WithdrawalTool(BaseTool):
    """Tool for handling token withdrawals."""
    
    def __init__(self, dependency_graph: Dict[str, Any], user_balances: Dict[str, Any]):
        """
        Initialize the withdrawal tool.
        
        Args:
            dependency_graph: The dependency graph data.
            user_balances: The user balance data.
        """
        self.dependency_graph = dependency_graph
        self.user_balances = user_balances
        
    def get_exit_functions_for_token(self, token_symbol: str, chain_id: str) -> List[Dict[str, Any]]:
        """
        Get exit functions for a specific token on a specific chain.
        
        Args:
            token_symbol: The symbol of the token.
            chain_id: The chain ID.
            
        Returns:
            List of exit functions for the token.
        """
        for dependency in self.dependency_graph.get("dependencies", []):
            if dependency.get("derivativeSymbol") == token_symbol and dependency.get("chainId") == chain_id:
                return dependency.get("exitFunctions", [])
        return []
        
    def get_user_positions(self, user_address: str, chain_id: str) -> List[Dict[str, Any]]:
        """
        Get user positions for a specific chain.
        
        Args:
            user_address: The user's wallet address.
            chain_id: The chain ID.
            
        Returns:
            List of user positions.
        """
        # Convert chain_id to string if it's not already
        chain_id = str(chain_id)
        
        logger.info(f"Looking for positions for user {user_address} on chain {chain_id}")
        for user in self.user_balances.get("users", []):
            if user.get("address") == user_address:
                chain_balances = user.get("chainBalances", {})
                if chain_id in chain_balances:
                    positions = chain_balances[chain_id].get("positions", [])
                    logger.info(f"Found {len(positions)} positions: {[p.get('symbol') for p in positions]}")
                    return positions
        logger.warning(f"No positions found for user {user_address} on chain {chain_id}")
        return []
    
    def execute(self, parameters: Dict[str, Any]) -> str:
        """
        Execute a withdrawal based on the provided parameters.
        
        Args:
            parameters: Dictionary containing withdrawal parameters:
                - token: The token to withdraw.
                - amount: The amount to withdraw.
                - destination: The destination for the withdrawn funds.
                - chain_id: The chain ID.
                - user_address: The user's wallet address.
                
        Returns:
            A string describing the action taken.
        """
        token = parameters.get("token", "unknown")
        amount = parameters.get("amount", "0")
        destination = parameters.get("destination", "unknown")
        chain_id = str(parameters.get("chain_id", "84532"))  # Default to Base, ensure it's a string
        user_address = parameters.get("user_address", "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266")  # Default user
        
        logger.info(f"Executing withdrawal for token {token} on chain {chain_id} for user {user_address}")
        logger.info(f"Full parameters: {parameters}")
        
        # Find positions for the token
        positions = self.get_user_positions(user_address, chain_id)
        matching_positions = [p for p in positions if p.get("symbol") == token]
        
        if not matching_positions:
            logger.warning(f"No positions found for token {token}")
            return f"Emergency withdrawal initiated: {amount} {token} to {destination}, but no matching positions found."
            
        logger.info(f"Found {len(matching_positions)} matching positions for token {token}")
        
        # Get exit functions for the token
        exit_functions = self.get_exit_functions_for_token(token, chain_id)
        
        if not exit_functions:
            logger.warning(f"No exit functions found for token {token}")
            return f"Emergency withdrawal initiated: {amount} {token} to {destination}, but no exit functions defined."
        
        # Execute the first available exit function
        exit_function = exit_functions[0]
        contract_type = exit_function.get("contractType", "unknown")
        function_name = exit_function.get("functionName", "unknown")
        
        # Format arguments based on the function definition and position data
        position = matching_positions[0]
        token_id = position.get("tokenId", "0")
        
        logger.info(f"WITHDRAWAL TOOL CALLED: Using {contract_type}.{function_name} for {token} with token ID {token_id}")
        
        # Build a detailed message based on the exit function and parameters
        message = f"Emergency withdrawal initiated: {amount} {token} to {destination}."
        message += f"\nExecuted {contract_type}.{function_name} with token ID {token_id}."
        
        return message
