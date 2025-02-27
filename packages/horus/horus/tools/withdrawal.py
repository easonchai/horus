"""
Withdrawal tool for the Horus security system.
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional

from .base import create_tool
from .constants import DEFAULT_BLOCK_EXPLORERS, DEFAULT_CHAIN_ID

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# Define a mock for the Coinbase AgentKit if not available
try:
    from coinbase_agentkit.action_providers.cdp.cdp_action_provider import \
        CdpActionProvider
    from coinbase_agentkit.action_providers.cdp.cdp_wallet_provider import \
        CdpWalletProvider
    from coinbase_agentkit.types import ActionResult, ActionStatus
    AGENTKIT_AVAILABLE = True
except ImportError:
    logger.warning("Coinbase AgentKit not available. Using mock implementation.")
    AGENTKIT_AVAILABLE = False
    
    # Create mock classes for testing
    class MockActionStatus:
        SUCCESS = "SUCCESS"
        FAILURE = "FAILURE"
    
    class MockActionResult:
        def __init__(self, success=True, transaction_hash="0xabcdef1234567890", message="Mock transaction successful"):
            self.success = success
            self.transaction_hash = transaction_hash
            self.message = message
    
    # Create mock modules
    ActionStatus = MockActionStatus()
    ActionResult = MockActionResult


class WithdrawalTool:
    """
    Tool for executing withdrawals from various protocols using Coinbase AgentKit.
    
    This tool allows for emergency withdrawals from protocols like Beefy and UniswapV3
    by:
    1. Identifying user positions on specific chains
    2. Finding appropriate exit functions for the token/protocol
    3. Executing the withdrawal using Coinbase AgentKit
    """
    
    def __init__(self, dependency_graph: Dict[str, Any], user_balances: Dict[str, Any], protocols_config: Dict[str, Any]):
        """
        Initialize the withdrawal tool with necessary configurations.
        
        Args:
            dependency_graph: Graph of token dependencies and exit functions
            user_balances: User balance data with positions
            protocols_config: Protocol ABIs and contract addresses
        """
        self.dependency_graph = dependency_graph or {}
        self.user_balances = user_balances or {}
        self.protocols_config = protocols_config or {"protocols": []}
        
        # Log the availability of AgentKit
        if AGENTKIT_AVAILABLE:
            logger.info("Coinbase AgentKit is available for real withdrawals")
        else:
            logger.info("Using simulation mode for withdrawals (AgentKit not available)")
    
    def get_user_positions(self, user_address: str, chain_id: str) -> List[Dict[str, Any]]:
        """
        Get positions for a user on a specific chain.
        
        Args:
            user_address: The user's address.
            chain_id: The chain ID.
            
        Returns:
            A list of user positions.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        if not self.user_balances:
            logger.warning("User balances not loaded")
            return []
        
        user_data = self.user_balances.get(user_address, {})
        chain_data = user_data.get(chain_id, {})
        return chain_data.get("positions", [])
    
    def get_exit_functions_for_token(self, token: str, chain_id: str) -> List[Dict[str, Any]]:
        """
        Get exit functions for a token on a specific chain.
        
        Args:
            token: The token symbol.
            chain_id: The chain ID.
            
        Returns:
            A list of exit functions.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        if not self.dependency_graph:
            logger.warning("Dependency graph not loaded")
            return []
        
        # Find the token in the dependency graph
        for node in self.dependency_graph.get("nodes", []):
            if node.get("symbol") == token and str(node.get("chainId")) == chain_id:
                return node.get("exitFunctions", [])
        
        return []
    
    def get_protocol_contract(self, protocol_name: str, contract_key: str, chain_id: str) -> Optional[str]:
        """
        Get a protocol contract address for a specific chain.
        
        Args:
            protocol_name: The name of the protocol (e.g., "Beefy", "UniswapV3")
            contract_key: The key for the specific contract
            chain_id: The chain ID as a string
            
        Returns:
            Contract address or None if not found
        """
        chain_id = str(chain_id)
        
        for protocol in self.protocols_config.get("protocols", []):
            if protocol.get("name") == protocol_name:
                chains = protocol.get("chains", {})
                if chain_id in chains:
                    return chains[chain_id].get(contract_key)
        
        return None
    
    def get_protocol_abi(self, protocol_name: str, contract_type: str) -> List[Dict[str, Any]]:
        """
        Get the ABI for a specific protocol contract type.
        
        Args:
            protocol_name: The name of the protocol (e.g., "Beefy", "UniswapV3")
            contract_type: The contract type (e.g., "BeefyVault", "NonfungiblePositionManager")
            
        Returns:
            The ABI as a list of dictionaries or an empty list if not found
        """
        for protocol in self.protocols_config.get("protocols", []):
            if protocol.get("name") == protocol_name:
                abis = protocol.get("abis", {})
                return abis.get(contract_type, [])
        
        return []
    
    def execute_withdrawal_with_agentkit(self, protocol: str, contract_address: str, function_name: str, 
                                  args: List[Any], chain_id: str) -> Dict[str, Any]:
        """
        Execute a withdrawal using Coinbase AgentKit.
        
        Args:
            protocol: The protocol name (e.g., "Beefy", "UniswapV3")
            contract_address: The contract address to interact with
            function_name: The function to call
            args: Arguments for the function
            chain_id: The chain ID
            
        Returns:
            Result of the execution
        """
        if not AGENTKIT_AVAILABLE:
            logger.warning(f"Simulating withdrawal from {protocol} using {function_name} on {contract_address}")
            return {
                "success": True,
                "transaction_hash": "0xabcdef1234567890",
                "message": f"Simulated withdrawal from {protocol} using {function_name}"
            }
        
        try:
            # Use the real AgentKit if available
            if not hasattr(self, '_cdp_action_provider'):
                self._cdp_action_provider = CdpActionProvider()
                self._cdp_wallet_provider = CdpWalletProvider()
            
            # Execute the contract write operation using AgentKit
            result = self._cdp_action_provider.execute_contract_write(
                chain_id=chain_id,
                account=self._cdp_wallet_provider.get_default_account(),
                contract_address=contract_address,
                function_name=function_name,
                args=args
            )
            
            return {
                "success": result.status == ActionStatus.SUCCESS,
                "transaction_hash": getattr(result, "transaction_hash", ""),
                "message": getattr(result, "message", "Withdrawal executed")
            }
            
        except Exception as e:
            logger.error(f"Error executing withdrawal with AgentKit: {str(e)}")
            return {
                "success": False,
                "transaction_hash": None,
                "message": f"Error: {str(e)}"
            }
    
    def execute_beefy_withdrawal(self, position: Dict[str, Any], chain_id: str) -> Dict[str, Any]:
        """
        Execute a withdrawal from a Beefy vault.
        
        Args:
            position: Position data including tokenId
            chain_id: The chain ID
            
        Returns:
            Result of the execution
        """
        protocol_name = "Beefy"
        contract_key = position.get("contractKey", "beefyUSDC-USDT-Vault")  # Default or from position
        token_id = position.get("tokenId")
        
        # Get contract address
        contract_address = self.get_protocol_contract(protocol_name, contract_key, chain_id)
        if not contract_address:
            return {
                "success": False,
                "message": f"Contract address not found for {protocol_name}.{contract_key} on chain {chain_id}"
            }
        
        # Execute withdrawal
        return self.execute_withdrawal_with_agentkit(
            protocol=protocol_name,
            contract_address=contract_address,
            function_name="withdraw",
            args=[token_id],
            chain_id=chain_id
        )
    
    def execute_uniswap_withdrawal(self, position: Dict[str, Any], chain_id: str) -> Dict[str, Any]:
        """
        Execute a withdrawal from a Uniswap V3 position.
        
        Args:
            position: Position data including tokenId and liquidity
            chain_id: The chain ID
            
        Returns:
            Result of the execution
        """
        protocol_name = "UniswapV3"
        token_id = position.get("tokenId")
        liquidity = position.get("liquidity", "0")
        
        # Get contract address for the position manager
        contract_address = self.get_protocol_contract(protocol_name, "nonfungiblePositionManager", chain_id)
        if not contract_address:
            return {
                "success": False,
                "message": f"Contract address not found for {protocol_name}.nonfungiblePositionManager on chain {chain_id}"
            }
        
        # First, decrease liquidity
        decrease_result = self.execute_withdrawal_with_agentkit(
            protocol=protocol_name,
            contract_address=contract_address,
            function_name="decreaseLiquidity",
            args=[
                token_id,           # tokenId
                liquidity,          # liquidity
                0,                  # amount0Min
                0,                  # amount1Min
                int(9999999999)     # deadline (far future)
            ],
            chain_id=chain_id
        )
        
        if not decrease_result.get("success"):
            return decrease_result
        
        # Then collect the tokens
        return self.execute_withdrawal_with_agentkit(
            protocol=protocol_name,
            contract_address=contract_address,
            function_name="collect",
            args=[
                token_id,                                   # tokenId
                "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",  # recipient (default or from params)
                2**128 - 1,                                # amount0Max (max uint128)
                2**128 - 1                                 # amount1Max (max uint128)
            ],
            chain_id=chain_id
        )
    
    def execute(self, parameters: Dict[str, Any]) -> str:
        """
        Execute a withdrawal operation based on the provided parameters.
        
        Args:
            parameters: Dictionary containing withdrawal parameters:
                - token: The token to withdraw.
                - amount: The amount to withdraw.
                - destination: The destination for the withdrawn funds.
                - chain_id: The chain ID.
                - user_address: The user's address.
                
        Returns:
            A string describing the action taken.
        """
        token = parameters.get("token", "unknown")
        amount = parameters.get("amount", "0")
        destination = parameters.get("destination", "unknown")
        chain_id = str(parameters.get("chain_id", DEFAULT_CHAIN_ID))  # Use the imported default chain ID
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
        
        # Process each matching position
        results = []
        for position in matching_positions:
            protocol = position.get("protocol", "unknown")
            
            if protocol.lower() == "beefy":
                result = self.execute_beefy_withdrawal(position, chain_id)
            elif protocol.lower() == "uniswap" or protocol.lower() == "uniswapv3":
                result = self.execute_uniswap_withdrawal(position, chain_id)
            else:
                # For unknown protocols, try to find an exit function and use it
                exit_functions = self.get_exit_functions_for_token(token, chain_id)
                
                if not exit_functions:
                    results.append({
                        "success": False,
                        "message": f"No exit functions found for {token} in protocol {protocol}"
                    })
                    continue
                
                # Use the first exit function
                exit_function = exit_functions[0]
                contract_type = exit_function.get("contractType", "unknown")
                function_name = exit_function.get("functionName", "unknown")
                contract_address = exit_function.get("contractAddress")
                
                if not contract_address:
                    results.append({
                        "success": False,
                        "message": f"No contract address found for {contract_type}.{function_name}"
                    })
                    continue
                
                # Execute the exit function
                token_id = position.get("tokenId", "0")
                result = self.execute_withdrawal_with_agentkit(
                    protocol=protocol,
                    contract_address=contract_address,
                    function_name=function_name,
                    args=[token_id],  # Simple case, just pass the token ID
                    chain_id=chain_id
                )
            
            results.append(result)
        
        # Build response message
        if not results:
            return f"Emergency withdrawal initiated: {amount} {token} to {destination}, but failed to execute any withdrawals."
        
        # Count successes and failures
        successes = sum(1 for r in results if r.get("success", False))
        failures = len(results) - successes
        
        message = f"Emergency withdrawal initiated: {amount} {token} to {destination}.\n"
        message += f"Results: {successes} successful, {failures} failed.\n"
        
        for i, result in enumerate(results):
            status = "Success" if result.get("success", False) else "Failed"
            tx_hash = result.get("transaction_hash", "N/A")
            result_msg = result.get("message", "No details")
            
            message += f"\n[{i+1}] {status}: {result_msg}"
            if tx_hash and tx_hash != "N/A":
                message += f" (TX: {tx_hash})"
        
        return message
    
    def __call__(self, parameters: Dict[str, Any]) -> str:
        """
        Make the class callable to maintain backwards compatibility.
        
        Args:
            parameters: Dictionary of parameters for the withdrawal.
            
        Returns:
            Response string from execute method.
        """
        return self.execute(parameters)


# Factory function to create a withdrawal tool
def create_withdrawal_tool(dependency_graph: Dict[str, Any], user_balances: Dict[str, Any], protocols_config: Dict[str, Any] = None) -> WithdrawalTool:
    """
    Create a withdrawal tool function.
    
    Args:
        dependency_graph: The dependency graph data.
        user_balances: The user balance data.
        protocols_config: The protocols configuration data.
        
    Returns:
        A function that can be called to execute withdrawals.
    """
    # If protocols_config is not provided, try to load it
    if protocols_config is None:
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            protocols_path = os.path.join(base_path, '..', '..', 'config', 'protocols.json')
            
            with open(protocols_path, 'r') as file:
                protocols_config = json.load(file)
        except Exception as e:
            logger.error(f"Error loading protocols config: {str(e)}")
            protocols_config = {"protocols": []}
    
    return WithdrawalTool(dependency_graph, user_balances, protocols_config)


# For backward compatibility, create a default instance
withdrawal_tool = create_withdrawal_tool({}, {})
