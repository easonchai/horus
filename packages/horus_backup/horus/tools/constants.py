"""
Shared constants for Horus security tools.

This module provides constants that are shared across multiple tools in the Horus system.
"""

# Default Chain ID for most operations
DEFAULT_CHAIN_ID = "84532"  # Base Sepolia Testnet

# Default block explorer URLs by chain ID
DEFAULT_BLOCK_EXPLORERS = {
    "1": "https://etherscan.io/tx/{}",           # Ethereum Mainnet
    "84532": "https://sepolia.basescan.org/tx/{}", # Base Sepolia Testnet
    "8453": "https://basescan.org/tx/{}",        # Base Mainnet
    "42161": "https://arbiscan.io/tx/{}",        # Arbitrum One
    "10": "https://optimistic.etherscan.io/tx/{}", # Optimism
    "137": "https://polygonscan.com/tx/{}",      # Polygon
}

# Default slippage settings for swaps
DEFAULT_SLIPPAGE = 0.5  # 0.5%

# Default fee tier for Uniswap V3 (0.3%)
DEFAULT_FEE_TIER = 3000

# CoinGecko API base URL for price data
COINGECKO_BASE_URL = "https://api.coingecko.com/api/v3"

# Valid swap sources
VALID_SWAP_SOURCES = ["UniswapV3", "SushiSwap", "Curve", "Balancer", "PancakeSwap"] 