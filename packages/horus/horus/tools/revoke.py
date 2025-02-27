"""
Revoke tool for the Horus security system.
Uses Coinbase AgentKit for token approval revocation.

This module provides a tool for revoking token approvals using Coinbase's AgentKit.
It supports multiple EVM networks and provides detailed transaction information.
"""
import logging
import os
from typing import Any, Dict, Optional, Tuple, TypedDict, Union

from coinbase_agentkit.action_providers.cdp.cdp_action_provider import \
    CdpActionProvider
from coinbase_agentkit.action_providers.cdp.cdp_wallet_provider import \
    CdpWalletProvider
from coinbase_agentkit.types import ActionResult, ActionStatus

from .base import BaseTool

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
    
    # Class constants
    DEFAULT_CHAIN_ID = "84532"  # Base Sepolia Testnet
    
    # Default block explorer URLs by chain ID in case they're not in the config
    DEFAULT_BLOCK_EXPLORERS = {
        "1": "https://etherscan.io/tx/{}",           # Ethereum Mainnet
        "84532": "https://sepolia.basescan.org/tx/{}", # Base Sepolia Testnet
        "8453": "https://basescan.org/tx/{}",        # Base Mainnet
        "42161": "https://arbiscan.io/tx/{}",        # Arbitrum One
        "10": "https://optimistic.etherscan.io/tx/{}", # Optimism
        "137": "https://polygonscan.com/tx/{}",      # Polygon
    }
    
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
        explorers = self.DEFAULT_BLOCK_EXPLORERS.copy()
        
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
        if self.DEFAULT_CHAIN_ID in chain_ids:
            return self.DEFAULT_CHAIN_ID
            
        # If the default is not available, use the first chain ID from the config
        if chain_ids:
            default_chain = next(iter(chain_ids))
            logger.info("Using chain ID %s from protocols config as default", default_chain)
            return default_chain
            
        # Fall back to the hardcoded default
        return self.DEFAULT_CHAIN_ID
    
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
        if self.wallet_provider is None or self.action_provider is None:
            # Get API key from environment
            api_key_name = os.environ.get("CDP_API_KEY_NAME")
            api_key_private_key = os.environ.get("CDP_API_KEY_PRIVATE_KEY")
            
            if not api_key_name or not api_key_private_key:
                raise ValueError(
                    "CDP_API_KEY_NAME and CDP_API_KEY_PRIVATE_KEY environment variables must be set"
                )
            
            try:
                # Initialize wallet provider
                logger.debug("Initializing CDP wallet provider")
                self.wallet_provider = CdpWalletProvider(
                    api_key_name=api_key_name,
                    api_key_private_key=api_key_private_key,
                )
                
                # Initialize action provider
                logger.debug("Initializing CDP action provider")
                self.action_provider = CdpActionProvider(
                    wallet_provider=self.wallet_provider,
                )
            except Exception as e:
                logger.error("Failed to initialize providers: %s", str(e))
                raise ConnectionError(f"Failed to initialize CDP providers: {str(e)}") from e
        
        return self.wallet_provider, self.action_provider

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
        # Extract parameters
        token_address = parameters.get("token_address", "unknown")
        spender_address = parameters.get("spender_address")
        protocol = parameters.get("protocol", "unknown")
        chain_id = str(parameters.get("chain_id", self.get_default_chain_id()))
        
        # If we only have the token symbol, try to look up the address
        if token_address == "unknown" and "token" in parameters:
            token_symbol = parameters.get("token", "")
            token_address = self.get_token_address(token_symbol, chain_id)
            logger.info("Resolved token symbol %s to address %s on chain %s", 
                       token_symbol, token_address, chain_id)
        
        # Validate parameters
        if token_address == "unknown":
            logger.error("Token address is required for revocation")
            return "Error: Token address is required for revocation. Please provide either a token_address or a valid token symbol."
        
        if not spender_address:
            logger.error("Spender address is required for revocation")
            return "Error: Spender address is required for revocation. Please provide the spender_address parameter."
        
        # Validate that addresses are in correct format (0x followed by 40 hex characters)
        if not self._is_valid_eth_address(token_address):
            logger.error("Invalid token address format: %s", token_address)
            return f"Error: Invalid token address format: {token_address}. Address should be in the format 0x followed by 40 hex characters."
            
        if not self._is_valid_eth_address(spender_address):
            logger.error("Invalid spender address format: %s", spender_address)
            return f"Error: Invalid spender address format: {spender_address}. Address should be in the format 0x followed by 40 hex characters."
        
        # Validate chain_id is numeric
        try:
            int(chain_id)
        except ValueError:
            logger.error("Invalid chain ID: %s", chain_id)
            return f"Error: Invalid chain ID: {chain_id}. Chain ID should be a numeric value."
            
        # Validate protocol
        if protocol != "unknown":
            protocol_info = self.get_protocol_info(protocol, chain_id)
            if protocol_info is None:
                logger.error("Unknown protocol %s", protocol)
                return f"Error: Unknown protocol {protocol}. Please provide a valid protocol name."
        
        logger.info("Executing revocation for token %s from spender %s on chain %s", 
                   token_address, spender_address, chain_id)
        
        try:
            # Initialize providers
            wallet_provider, action_provider = self.initialize_providers()
            
            # Get the wallet
            wallet = wallet_provider.get_wallet()
            if not wallet:
                logger.error("Failed to initialize wallet")
                return "Error: Failed to initialize wallet. Please check your API credentials."
            
            # Create the revoke action
            revoke_action = self.create_revoke_action(token_address, spender_address, chain_id)
            
            # Execute the revoke action
            logger.debug("Executing revoke action: %s", revoke_action)
            result: ActionResult = action_provider.execute_action(revoke_action)
            
            # Check the result
            if result.status == ActionStatus.SUCCESS:
                tx_hash = result.result.get("transactionHash", "unknown")
                explorer_url = self.get_explorer_url(chain_id, tx_hash)
                
                logger.info("Successfully revoked approval. Transaction hash: %s", tx_hash)
                
                message = f"Successfully revoked approval for {token_address} from {spender_address} on chain {chain_id}."
                if protocol != "unknown":
                    message += f" This prevents the {protocol} protocol from accessing your tokens."
                
                if explorer_url:
                    message += f"\nTransaction: {explorer_url}"
                
                return message
            else:
                error = result.error or "Unknown error"
                logger.error("Failed to revoke approval: %s", error)
                return f"Failed to revoke approval: {error}"
            
        except ValueError as e:
            logger.error("Value error during revocation: %s", str(e))
            return f"Error: {str(e)}"
        except ConnectionError as e:
            logger.error("Connection error during revocation: %s", str(e))
            return f"Error connecting to CDP API: {str(e)}"
        except Exception as e:
            logger.error("Unexpected error executing revocation: %s", str(e))
            return f"Error executing revocation: {str(e)}"

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
