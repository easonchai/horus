"""
Swap tool for the Horus security system.
"""
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple

from .base import create_tool

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
        def __init__(self, status="SUCCESS", transaction_hash="0xabcdef1234567890", message="Mock transaction successful"):
            self.status = status
            self.transaction_hash = transaction_hash
            self.message = message
    
    # Create mock modules
    ActionStatus = MockActionStatus()
    ActionResult = MockActionResult


class SwapTool:
    """
    Tool for executing token swaps using Coinbase AgentKit.
    
    This tool allows for swapping one token for another across various DEXes:
    1. Identifying available token pairs on supported DEXes
    2. Calculating swap quotes
    3. Executing the swap using Coinbase AgentKit
    """
    
    def __init__(self, tokens_config: Dict[str, Any], protocols_config: Dict[str, Any], dependency_graph: Dict[str, Any]):
        """
        Initialize the swap tool with necessary configurations.
        
        Args:
            tokens_config: Token configuration with addresses
            protocols_config: Protocol ABIs and contract addresses
            dependency_graph: Graph of token dependencies
        """
        self.tokens_config = tokens_config or {"tokens": []}
        self.protocols_config = protocols_config or {"protocols": []}
        self.dependency_graph = dependency_graph or {}
        
        # Log the availability of AgentKit
        if AGENTKIT_AVAILABLE:
            logger.info("Coinbase AgentKit is available for real swaps")
        else:
            logger.info("Using simulation mode for swaps (AgentKit not available)")
        
        # Cache for token addresses
        self._token_address_cache = {}
    
    def get_token_address(self, token_symbol: str, chain_id: str) -> Optional[str]:
        """
        Get the contract address for a token on a specific chain.
        
        Args:
            token_symbol: The symbol of the token.
            chain_id: The chain ID.
            
        Returns:
            Token contract address or None if not found.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        cache_key = f"{token_symbol}:{chain_id}"
        
        # Check cache first
        if cache_key in self._token_address_cache:
            return self._token_address_cache[cache_key]
        
        # Look up token address
        for token in self.tokens_config.get("tokens", []):
            if token.get("symbol") == token_symbol:
                networks = token.get("networks", {})
                address = networks.get(chain_id)
                if address:
                    self._token_address_cache[cache_key] = address
                    return address
        
        return None
    
    def get_dex_router(self, dex_name: str, chain_id: str) -> Optional[str]:
        """
        Get the router contract address for a DEX on a specific chain.
        
        Args:
            dex_name: The name of the DEX (e.g., "UniswapV3", "SushiSwap")
            chain_id: The chain ID.
            
        Returns:
            Router contract address or None if not found.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        for protocol in self.protocols_config.get("protocols", []):
            if protocol.get("name").lower() == dex_name.lower():
                chains = protocol.get("chains", {})
                if chain_id in chains:
                    # Look for router or swapRouter key 
                    router = chains[chain_id].get("router") or chains[chain_id].get("swapRouter")
                    if router:
                        return router
        
        return None
    
    def execute_swap_with_agentkit(
        self, 
        token_in_address: str, 
        token_out_address: str,
        amount_in: str, 
        min_amount_out: str,
        router_address: str,
        chain_id: str,
        slippage: float = 0.5
    ) -> Dict[str, Any]:
        """
        Execute a token swap using Coinbase AgentKit.
        
        Args:
            token_in_address: The address of the input token
            token_out_address: The address of the output token
            amount_in: The amount of input tokens to swap
            min_amount_out: The minimum amount of output tokens to receive
            router_address: The address of the DEX router
            chain_id: The chain ID
            slippage: Maximum acceptable slippage percentage
            
        Returns:
            Result of the execution
        """
        if not AGENTKIT_AVAILABLE:
            logger.warning(f"Simulating swap from {token_in_address} to {token_out_address} on chain {chain_id}")
            return {
                "success": True,
                "transaction_hash": "0xabcdef1234567890",
                "message": f"Simulated swap of {amount_in} tokens for approximately {min_amount_out} tokens with {slippage}% slippage"
            }
        
        try:
            # Use the real AgentKit if available
            if not hasattr(self, '_cdp_action_provider'):
                self._cdp_action_provider = CdpActionProvider()
                self._cdp_wallet_provider = CdpWalletProvider()
            
            # Get default account
            account = self._cdp_wallet_provider.get_default_account()
            
            # Execute the swap using AgentKit
            result = self._cdp_action_provider.execute_swap(
                chain_id=chain_id,
                account=account,
                token_in=token_in_address,
                token_out=token_out_address,
                amount_in=amount_in,
                slippage_percentage=slippage,
                fee_tier=3000  # Default fee tier (0.3%)
            )
            
            return {
                "success": result.status == ActionStatus.SUCCESS,
                "transaction_hash": getattr(result, "transaction_hash", ""),
                "message": getattr(result, "message", "Swap executed"),
                "amount_in": amount_in,
                "amount_out": getattr(result, "amount_out", min_amount_out)
            }
            
        except Exception as e:
            logger.error(f"Error executing swap with AgentKit: {str(e)}")
            return {
                "success": False,
                "transaction_hash": None,
                "message": f"Error: {str(e)}"
            }
    
    def get_default_dex(self, chain_id: str) -> str:
        """
        Get the default DEX to use for a specific chain.
        
        Args:
            chain_id: The chain ID
            
        Returns:
            Name of the default DEX for the chain
        """
        # Map chain IDs to default DEXes
        chain_id = str(chain_id)
        chain_to_dex = {
            "1": "UniswapV3",      # Ethereum
            "84532": "UniswapV3",  # Base
            "42161": "UniswapV3",  # Arbitrum
            "10": "UniswapV3",     # Optimism
            "8453": "UniswapV3",   # Base
            "137": "QuickSwap",    # Polygon
        }
        
        return chain_to_dex.get(chain_id, "UniswapV3")
    
    def estimate_output_amount(
        self, 
        token_in: str, 
        token_out: str, 
        amount_in: str, 
        chain_id: str
    ) -> str:
        """
        Estimate the output amount for a swap.
        
        Args:
            token_in: The input token symbol
            token_out: The output token symbol
            amount_in: The amount of input tokens
            chain_id: The chain ID
            
        Returns:
            Estimated output amount
        """
        # In a real implementation, this would call a price API or on-chain quote
        # Here we simulate a simple estimate with 2% slippage
        
        # For demo purposes, use a simple calculation
        # In reality, you would use a price feed or on-chain quote
        token_in_lower = token_in.lower()
        token_out_lower = token_out.lower()
        
        # Simplified price ratios for common tokens
        price_ratios = {
            "eth:usdc": 1800,    # 1 ETH = 1800 USDC
            "usdc:eth": 1/1800,  # 1 USDC = 0.00055 ETH
            "wbtc:usdc": 40000,  # 1 WBTC = 40000 USDC
            "usdc:wbtc": 1/40000,# 1 USDC = 0.000025 WBTC
            "eth:wbtc": 0.045,   # 1 ETH = 0.045 WBTC
            "wbtc:eth": 22.2,    # 1 WBTC = 22.2 ETH
            "usdt:usdc": 1,      # 1 USDT = 1 USDC
            "usdc:usdt": 1,      # 1 USDC = 1 USDT
        }
        
        ratio_key = f"{token_in_lower}:{token_out_lower}"
        
        if ratio_key in price_ratios:
            ratio = price_ratios[ratio_key]
        else:
            # Default to 1:1 for unknown pairs
            ratio = 1
        
        try:
            amount_in_float = float(amount_in)
            estimated_output = amount_in_float * ratio * 0.98  # Apply 2% slippage
            return str(estimated_output)
        except (ValueError, TypeError):
            logger.error(f"Error converting amount_in to float: {amount_in}")
            return "0"
    
    def execute(self, parameters: Dict[str, Any]) -> str:
        """
        Execute a token swap based on the provided parameters.
        
        Args:
            parameters: Dictionary containing swap parameters:
                - token_in: The input token symbol
                - token_out: The output token symbol
                - amount_in: The amount of input tokens to swap
                - chain_id: The chain ID
                - dex: (optional) The DEX to use for the swap
                - slippage: (optional) Maximum acceptable slippage percentage
                
        Returns:
            A string describing the action taken.
        """
        # Extract parameters
        token_in = parameters.get("token_in")
        token_out = parameters.get("token_out")
        amount_in = parameters.get("amount_in", "0")
        chain_id = str(parameters.get("chain_id", "84532"))  # Default to Base, ensure it's a string
        dex = parameters.get("dex", self.get_default_dex(chain_id))
        slippage = float(parameters.get("slippage", 0.5))
        
        logger.info(f"Executing swap from {token_in} to {token_out} on chain {chain_id} using {dex}")
        logger.info(f"Full parameters: {parameters}")
        
        # Validate required parameters
        if not token_in or not token_out:
            return "Error: Missing required parameters 'token_in' and 'token_out'"
        
        # Get token addresses
        token_in_address = self.get_token_address(token_in, chain_id)
        token_out_address = self.get_token_address(token_out, chain_id)
        
        if not token_in_address:
            return f"Error: Could not find address for token {token_in} on chain {chain_id}"
        
        if not token_out_address:
            return f"Error: Could not find address for token {token_out} on chain {chain_id}"
        
        # Get DEX router address
        router_address = self.get_dex_router(dex, chain_id)
        if not router_address:
            return f"Error: Could not find router address for {dex} on chain {chain_id}"
        
        # Estimate output amount
        estimated_output = self.estimate_output_amount(token_in, token_out, amount_in, chain_id)
        
        # Calculate minimum output with slippage
        min_amount_out = str(float(estimated_output) * (1 - slippage / 100))
        
        # Execute the swap
        result = self.execute_swap_with_agentkit(
            token_in_address=token_in_address,
            token_out_address=token_out_address,
            amount_in=amount_in,
            min_amount_out=min_amount_out,
            router_address=router_address,
            chain_id=chain_id,
            slippage=slippage
        )
        
        # Build response message
        if result.get("success"):
            message = f"Successfully swapped {amount_in} {token_in} for approximately {result.get('amount_out', min_amount_out)} {token_out}"
            if result.get("transaction_hash"):
                message += f"\nTransaction: {result['transaction_hash']}"
        else:
            message = f"Failed to swap {token_in} for {token_out}: {result.get('message', 'Unknown error')}"
        
        return message
    
    def __call__(self, parameters: Dict[str, Any]) -> str:
        """
        Make the class callable to maintain backwards compatibility.
        
        Args:
            parameters: Dictionary of parameters for the swap.
            
        Returns:
            Response string from execute method.
        """
        return self.execute(parameters)


# Factory function to create a swap tool
def create_swap_tool(tokens_config: Dict[str, Any], protocols_config: Dict[str, Any], dependency_graph: Dict[str, Any] = None) -> SwapTool:
    """
    Create a swap tool.
    
    Args:
        tokens_config: Token configuration with addresses
        protocols_config: Protocol ABIs and contract addresses
        dependency_graph: Graph of token dependencies
        
    Returns:
        A SwapTool instance that can be called to execute swaps.
    """
    # If dependency_graph is not provided, try to load it
    if dependency_graph is None:
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            graph_path = os.path.join(base_path, '..', '..', 'config', 'dependency_graph.json')
            
            with open(graph_path, 'r') as file:
                dependency_graph = json.load(file)
        except Exception as e:
            logger.error(f"Error loading dependency graph: {str(e)}")
            dependency_graph = {}
    
    return SwapTool(tokens_config, protocols_config, dependency_graph)


# For backward compatibility, create a default instance
swap_tool = create_swap_tool({}, {}) 