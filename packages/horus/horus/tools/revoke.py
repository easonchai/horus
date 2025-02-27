"""
Revoke tool for the Horus security system.
Uses Coinbase AgentKit for token approval revocation.

This module provides a tool for revoking token approvals using Coinbase's AgentKit.
It supports multiple EVM networks and provides detailed transaction information.
"""
import logging
import os
from typing import Any, Dict, Optional, Tuple, TypedDict, Union

# Try to import Coinbase AgentKit, but provide mock implementations if not available
try:
    from coinbase_agentkit.action_providers.cdp.cdp_action_provider import CdpActionProvider
    from coinbase_agentkit.action_providers.cdp.cdp_wallet_provider import CdpWalletProvider
    from coinbase_agentkit.types import ActionResult, ActionStatus
    COINBASE_AGENTKIT_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Coinbase AgentKit not available. Using mock implementations.")
    COINBASE_AGENTKIT_AVAILABLE = False
    
    # Define mock classes
    class CdpWalletProvider:
        def __init__(self, *args, **kwargs):
            pass
    
    class CdpActionProvider:
        def __init__(self, *args, **kwargs):
            pass
        
        def execute_action(self, *args, **kwargs):
            return {
                "status": "COMPLETED",
                "message": "Mock implementation: Coinbase AgentKit not available",
                "transaction_hash": "0x0000000000000000000000000000000000000000000000000000000000000000"
            }
    
    class ActionResult:
        pass
    
    class ActionStatus:
        COMPLETED = "COMPLETED"
        ERROR = "ERROR"

from .base import BaseTool
from .constants import DEFAULT_BLOCK_EXPLORERS, DEFAULT_CHAIN_ID

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


class RevokeParameters(TypedDict, total=False):
    """Type definition for revoke parameters."""
    token_address: str
    spender_address: str
    protocol: str
    chain_id: Union[str, int]
    token: str


class RevokeTool(BaseTool):
    """
    Tool for revoking token approvals using Coinbase AgentKit.
    
    This tool allows for the revocation of token approvals (allowances) that have been
    previously granted to spender addresses. It uses Coinbase's AgentKit to interact
    with the blockchain and execute the revocation transactions.
    
    Example:
        ```python
        # Create a revoke tool with token configuration
        tokens_config = {
            "tokens": [
                {
                    "symbol": "USDC",
                    "networks": {
                        "1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                        "8453": "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
                    }
                }
            ]
        }
        protocols_config = {
            "protocols": [
                {
                    "name": "UniswapV3",
                    "chains": {
                        "1": {...},
                        "8453": {...}
                    }
                }
            ]
        }
        revoke_tool = RevokeTool(tokens_config, protocols_config)
        
        # Execute a revocation
        result = revoke_tool.execute({
            "token": "USDC",
            "spender_address": "0x1234...",
            "chain_id": "8453"
        })
        ```
    """
    
    # Class constants - use imported constants
    
    def __init__(self, tokens_config: Dict[str, Any], protocols_config: Optional[Dict[str, Any]] = None):
        """
        Initialize the RevokeTool with token and protocol configuration.
        
        Args:
            tokens_config: Dictionary containing token configuration data.
                Expected format:
                {
                    "tokens": [
                        {
                            "symbol": "TOKEN_SYMBOL",
                            "networks": {
                                "CHAIN_ID": "CONTRACT_ADDRESS",
                                ...
                            }
                        },
                        ...
                    ]
                }
            protocols_config: Optional dictionary containing protocol configuration data.
                Expected format:
                {
                    "protocols": [
                        {
                            "name": "PROTOCOL_NAME",
                            "chains": {
                                "CHAIN_ID": { ... },
                                ...
                            }
                        },
                        ...
                    ]
                }
        """
        super().__init__("revoke")
        self.tokens_config = tokens_config
        self.protocols_config = protocols_config or {"protocols": []}
        self.wallet_provider: Optional[CdpWalletProvider] = None
        self.action_provider: Optional[CdpActionProvider] = None
        
        # Build block explorer mapping from protocols config
        self.block_explorers = self._build_block_explorer_mapping()
        
        # Log initialization info
        logger.debug("RevokeTool initialized with %d tokens", len(tokens_config.get("tokens", [])))
        logger.debug("RevokeTool initialized with %d protocols", len(self.protocols_config.get("protocols", [])))
        
    def _build_block_explorer_mapping(self) -> Dict[str, str]:
        """
        Build a mapping of chain IDs to block explorer URLs from the protocols configuration.
        Falls back to default explorers if not specified in the config.
        
        Returns:
            A dictionary mapping chain IDs to block explorer URL templates.
        """
        # Start with default explorers
        explorers = DEFAULT_BLOCK_EXPLORERS.copy()
        
        # Try to extract explorer URLs from protocols config
        # This is a simplistic approach - in a real implementation, you might
        # want to analyze the protocols config in more detail
        chain_ids = set()
        for protocol in self.protocols_config.get("protocols", []):
            for chain_id in protocol.get("chains", {}).keys():
                chain_ids.add(chain_id)
        
        # For now, we'll stick with our default explorers
        # In a complete implementation, you would extract the explorer URLs
        # from your protocols configuration if available
        
        logger.debug("Block explorer mapping built for %d chains", len(explorers))
        return explorers
        
    def get_default_chain_id(self) -> str:
        """
        Get the default chain ID from the protocols configuration.
        Falls back to the DEFAULT_CHAIN_ID if not available.
        
        Returns:
            The default chain ID as a string.
        """
        # Get all chain IDs from protocols config
        chain_ids = set()
        for protocol in self.protocols_config.get("protocols", []):
            for chain_id in protocol.get("chains", {}).keys():
                chain_ids.add(chain_id)
                
        # Look for the DEFAULT_CHAIN_ID in the available chains
        if DEFAULT_CHAIN_ID in chain_ids:
            return DEFAULT_CHAIN_ID
            
        # If the default is not available, use the first chain ID from the config
        if chain_ids:
            default_chain = next(iter(chain_ids))
            logger.info("Using chain ID %s from protocols config as default", default_chain)
            return default_chain
            
        # Fall back to the hardcoded default
        return DEFAULT_CHAIN_ID
    
    def get_token_address(self, token_symbol: str, chain_id: str) -> str:
        """
        Get the contract address for a token on a specific chain.
        
        Args:
            token_symbol: The symbol of the token (e.g., "USDC", "WETH").
            chain_id: The chain ID as a string (e.g., "1" for Ethereum Mainnet).
            
        Returns:
            Token contract address or "unknown" if not found.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        for token in self.tokens_config.get("tokens", []):
            if token.get("symbol") == token_symbol:
                networks = token.get("networks", {})
                address = networks.get(chain_id, "unknown")
                logger.debug("Found token address %s for %s on chain %s", address, token_symbol, chain_id)
                return address
        
        logger.warning("Token address not found for %s on chain %s", token_symbol, chain_id)
        return "unknown"
        
    def get_protocol_info(self, protocol_name: str, chain_id: str) -> Optional[Dict[str, Any]]:
        """
        Check if a protocol exists and supports a specific chain.
        
        Args:
            protocol_name: The name of the protocol (e.g., "UniswapV3").
            chain_id: The chain ID as a string (e.g., "1" for Ethereum Mainnet).
            
        Returns:
            The protocol configuration for the specified chain, or None if not found.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        for protocol in self.protocols_config.get("protocols", []):
            if protocol.get("name") == protocol_name:
                chains = protocol.get("chains", {})
                chain_config = chains.get(chain_id)
                
                if chain_config:
                    logger.debug("Found protocol %s configuration for chain %s", protocol_name, chain_id)
                    return chain_config
                else:
                    logger.warning("Protocol %s does not support chain %s", protocol_name, chain_id)
                    return None
        
        logger.warning("Protocol %s not found in configuration", protocol_name)
        return None
    
    def initialize_providers(self) -> Tuple[CdpWalletProvider, CdpActionProvider]:
        """
        Initialize the AgentKit wallet and action providers.
        
        Providers are initialized lazily when needed to avoid unnecessary API calls.
        API keys are retrieved from environment variables.
        
        Returns:
            A tuple of (wallet_provider, action_provider)
            
        Raises:
            ValueError: If required environment variables are not set.
            ConnectionError: If there's an issue connecting to the CDP API.
        """
        # If providers are already initialized, return them
        if self.wallet_provider and self.action_provider:
            return self.wallet_provider, self.action_provider
        
        # If Coinbase AgentKit is not available, return mock providers
        if not COINBASE_AGENTKIT_AVAILABLE:
            logger.warning("Using mock providers because Coinbase AgentKit is not available")
            self.wallet_provider = CdpWalletProvider()
            self.action_provider = CdpActionProvider()
            return self.wallet_provider, self.action_provider
        
        # Get API key details from environment variables
        api_key_name = os.getenv("CDP_API_KEY_NAME")
        api_key_private_key = os.getenv("CDP_API_KEY_PRIVATE_KEY")
        
        if not api_key_name or not api_key_private_key:
            raise ValueError(
                "CDP_API_KEY_NAME and CDP_API_KEY_PRIVATE_KEY environment variables must be set"
            )
        
        try:
            # Initialize the wallet provider
            self.wallet_provider = CdpWalletProvider(
                api_key_name=api_key_name,
                api_key_private_key=api_key_private_key,
            )
            
            # Initialize the action provider
            self.action_provider = CdpActionProvider(
                wallet_provider=self.wallet_provider,
            )
            
            logger.debug("CDP wallet and action providers initialized successfully")
            
            return self.wallet_provider, self.action_provider
            
        except Exception as e:
            logger.error(f"Failed to initialize CDP providers: {str(e)}")
            raise ConnectionError(f"Failed to connect to CDP API: {str(e)}")
    
    def get_explorer_url(self, chain_id: str, tx_hash: str) -> Optional[str]:
        """
        Get the block explorer URL for a transaction.
        
        Args:
            chain_id: The chain ID as a string (e.g., "1" for Ethereum Mainnet).
            tx_hash: The transaction hash.
            
        Returns:
            The block explorer URL or None if not available for the given chain.
        """
        explorer_template = self.block_explorers.get(chain_id)
        if explorer_template:
            return explorer_template.format(tx_hash)
        
        logger.warning("No block explorer found for chain ID %s", chain_id)
        return None
    
    def create_revoke_action(self, token_address: str, spender_address: str, chain_id: str) -> Dict[str, Any]:
        """
        Create a revoke action configuration for AgentKit.
        
        Args:
            token_address: The contract address of the token.
            spender_address: The address that has been approved to spend the token.
            chain_id: The chain ID as a string.
            
        Returns:
            A dictionary containing the revoke action configuration.
        """
        return {
            "type": "revokeAllowance",
            "params": {
                "tokenAddress": token_address,
                "spenderAddress": spender_address,
                "chainId": chain_id,
            }
        }
    
    def execute(self, parameters: RevokeParameters) -> str:
        """
        Execute a revocation operation based on the provided parameters using AgentKit.
        
        Args:
            parameters: Dictionary containing revocation parameters:
                - token_address: The contract address to revoke permissions from.
                - spender_address: The address that has been approved to spend the token.
                - protocol: The protocol to revoke permissions from (optional).
                - chain_id: The chain ID (default: 84532 for Base Sepolia).
                - token: The token symbol (optional, used if token_address not provided).
                
        Returns:
            A string describing the action taken or an error message.
            
        Raises:
            ValueError: If required parameters are missing.
            ConnectionError: If there's an issue connecting to the CDP API.
        """
        # If Coinbase AgentKit is not available, return a mock response
        if not COINBASE_AGENTKIT_AVAILABLE:
            token = parameters.get("token", "UNKNOWN")
            protocol = parameters.get("protocol", "UNKNOWN")
            chain_id = parameters.get("chain_id", DEFAULT_CHAIN_ID)
            
            logger.warning(f"Mock revocation executed for {token} on {protocol} (chain_id: {chain_id})")
            
            return (
                f"MOCK RESPONSE: Successfully revoked approval for {token} to {protocol} "
                f"on chain with ID {chain_id}. This is a mock response because Coinbase "
                f"AgentKit is not available. No actual blockchain transaction was executed."
            )
        
        # Log the parameters for debugging
        logger.info(f"Executing revoke tool with parameters: {parameters}")
        
        # Get token address from token symbol if not provided directly
        token_address = parameters.get("token_address")
        token_symbol = parameters.get("token")
        
        if not token_address and token_symbol:
            chain_id = str(parameters.get("chain_id", DEFAULT_CHAIN_ID))
            token_address = self.get_token_address(token_symbol, chain_id)
            
            # If token address is still not found, return an error
            if not token_address or token_address == "unknown":
                return f"ERROR: Token '{token_symbol}' not found for chain ID '{chain_id}'"
        
        # Get the spender address
        spender_address = parameters.get("spender_address")
        
        # Validate token address
        if not token_address:
            return "ERROR: Missing token address. Please provide either token_address or token in the parameters."
        
        # Validate spender address
        if not spender_address:
            return "ERROR: Missing spender address. Please provide spender_address in the parameters."
        
        # Validate that addresses are in the correct format
        if not self._is_valid_eth_address(token_address):
            return f"ERROR: Invalid token address format: {token_address}"
        
        if not self._is_valid_eth_address(spender_address):
            return f"ERROR: Invalid spender address format: {spender_address}"
        
        # Get chain ID (default to Base Sepolia)
        chain_id = str(parameters.get("chain_id", DEFAULT_CHAIN_ID))
        
        # Get protocol name (for logging)
        protocol = parameters.get("protocol", "Unknown Protocol")
        
        try:
            # Initialize providers
            wallet_provider, action_provider = self.initialize_providers()
            
            # Create the revoke action
            action = self.create_revoke_action(token_address, spender_address, chain_id)
            
            # Execute the action
            logger.info(f"Executing revocation for token {token_address} to spender {spender_address}")
            result = action_provider.execute_action(action)
            
            # Process the result
            status = result.get("status")
            message = result.get("message", "")
            tx_hash = result.get("transaction_hash", "")
            
            if status == ActionStatus.COMPLETED:
                # Build a response with block explorer link if available
                explorer_url = self.get_explorer_url(chain_id, tx_hash)
                
                explorer_message = ""
                if explorer_url:
                    explorer_message = f"View the transaction on block explorer: {explorer_url}"
                
                token_display = token_symbol if token_symbol else token_address
                
                return (
                    f"Successfully revoked approval for {token_display} to {protocol} "
                    f"on chain with ID {chain_id}.\n"
                    f"Transaction hash: {tx_hash}\n"
                    f"{explorer_message}"
                )
            else:
                return f"ERROR: Revocation failed: {message}"
                
        except ValueError as e:
            return f"ERROR: {str(e)}"
        except ConnectionError as e:
            return f"ERROR: Connection failed: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error in revoke tool: {str(e)}")
            return f"ERROR: Unexpected error: {str(e)}"
    
    def _is_valid_eth_address(self, address: str) -> bool:
        """
        Validate that a string is in the format of an Ethereum address.
        
        Args:
            address: The address to validate.
            
        Returns:
            True if the address is valid, False otherwise.
        """
        import re

        # Check if address is a string and matches the format 0x followed by 40 hex characters
        if not isinstance(address, str):
            return False
        return bool(re.match(r'^0x[a-fA-F0-9]{40}$', address))
