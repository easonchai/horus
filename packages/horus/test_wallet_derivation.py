#!/usr/bin/env python3
"""
Test script to validate wallet address derivation consistency across all tools.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Import the tools - we need the same CdpWalletProvider implementation from each module
from tools.withdrawal import WithdrawalTool, CdpWalletProvider as WithdrawalCdpWalletProvider
from tools.revoke import RevokeTool, CdpWalletProvider as RevokeCdpWalletProvider

def test_wallet_derivation():
    """Test if wallet address derivation is consistent across all tools."""
    logger.info("Testing wallet address derivation consistency...")
    
    # Create a test private key for environment if not already set
    if not os.getenv("PRIVATE_KEY"):
        test_private_key = "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
        os.environ["PRIVATE_KEY"] = test_private_key
        logger.info(f"Setting test PRIVATE_KEY: {test_private_key}")
    
    # Get the private key from environment
    private_key = os.getenv("PRIVATE_KEY")
    
    # Create wallet providers directly
    withdrawal_wallet = WithdrawalCdpWalletProvider(private_key=private_key)
    revoke_wallet = RevokeCdpWalletProvider(private_key=private_key)
    
    # Get wallet addresses from each provider
    withdrawal_address = withdrawal_wallet.get_wallet_address()
    revoke_address = revoke_wallet.get_wallet_address()
    
    # Print the addresses
    logger.info(f"Withdrawal Tool wallet address: {withdrawal_address}")
    logger.info(f"Revoke Tool wallet address: {revoke_address}")
    
    # Check if addresses are the same
    if withdrawal_address == revoke_address:
        logger.info("SUCCESS: Wallet addresses are consistent between WithdrawalTool and RevokeTool!")
        
        # Print detailed derivation info
        logger.info("-" * 80)
        logger.info("Wallet Address Derivation Details:")
        logger.info(f"Private Key (truncated): {private_key[:10]}...{private_key[-10:]}")
        logger.info(f"Derived Address: {withdrawal_address}")
        logger.info("-" * 80)
        
        return True
    else:
        logger.error("FAILURE: Wallet addresses are not consistent across tools!")
        logger.error(f"WithdrawalTool address: {withdrawal_address}")
        logger.error(f"RevokeTool address: {revoke_address}")
        return False

if __name__ == "__main__":
    if test_wallet_derivation():
        logger.info("All tests passed!")
        sys.exit(0)
    else:
        logger.error("Tests failed!")
        sys.exit(1)
