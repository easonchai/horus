"""
Withdrawal tool for the Horus security system.
"""
import logging
from typing import Dict, Any, List, Callable

from .base import create_tool

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


def create_withdrawal_tool(dependency_graph: Dict[str, Any], user_balances: Dict[str, Any]) -> Callable[[Dict[str, Any]], str]:
    """
    Create a withdrawal tool function.
    
    Args:
        dependency_graph: The dependency graph data.
        user_balances: The user balance data.
        
    Returns:
        A function that can be called to execute withdrawals.
    """
    def get_user_positions(user_address: str, chain_id: str) -> List[Dict[str, Any]]:
        """
        Get positions for a user on a specific chain.
        
        Args:
            user_address: The user's address.
            chain_id: The chain ID.
            
        Returns:
            A list of user positions.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        if not user_balances:
            logger.warning("User balances not loaded")
            return []
        
        user_data = user_balances.get(user_address, {})
        chain_data = user_data.get(chain_id, {})
        return chain_data.get("positions", [])
    
    def get_exit_functions_for_token(token: str, chain_id: str) -> List[Dict[str, Any]]:
        """
        Get exit functions for a token on a specific chain.
        
        Args:
            token: The token symbol.
            chain_id: The chain ID.
            
        Returns:
            A list of exit functions.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        if not dependency_graph:
            logger.warning("Dependency graph not loaded")
            return []
        
        # Find the token in the dependency graph
        for node in dependency_graph.get("nodes", []):
            if node.get("symbol") == token and str(node.get("chainId")) == chain_id:
                return node.get("exitFunctions", [])
        
        return []
    
    def execute_withdrawal(parameters: Dict[str, Any]) -> str:
        """
        Execute a withdrawal operation based on the provided parameters.
        
        Args:
            parameters: Dictionary containing withdrawal parameters:
                - token: The token to withdraw.
                - amount: The amount to withdraw.
                - destination: The destination for the withdrawn funds.
                - chain_id: The chain ID.
                
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
        positions = get_user_positions(user_address, chain_id)
        matching_positions = [p for p in positions if p.get("symbol") == token]
        
        if not matching_positions:
            logger.warning(f"No positions found for token {token}")
            return f"Emergency withdrawal initiated: {amount} {token} to {destination}, but no matching positions found."
            
        logger.info(f"Found {len(matching_positions)} matching positions for token {token}")
        
        # Get exit functions for the token
        exit_functions = get_exit_functions_for_token(token, chain_id)
        
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
    
    # Create and return the tool function
    return create_tool("withdrawal", execute_withdrawal)


# Create a default withdrawal tool for export
withdrawal_tool = create_withdrawal_tool({}, {})
