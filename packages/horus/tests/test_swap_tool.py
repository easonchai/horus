#!/usr/bin/env python3
"""
Test script for the Swap Tool.
"""
import json
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the coinbase_agentkit modules before importing SwapTool
sys.modules['coinbase_agentkit'] = MagicMock()
sys.modules['coinbase_agentkit.action_providers'] = MagicMock()
sys.modules['coinbase_agentkit.action_providers.cdp'] = MagicMock()
sys.modules['coinbase_agentkit.action_providers.cdp.cdp_action_provider'] = MagicMock()
sys.modules['coinbase_agentkit.action_providers.cdp.cdp_wallet_provider'] = MagicMock()
sys.modules['coinbase_agentkit.types'] = MagicMock()

# Create ActionStatus mock
mock_action_status = MagicMock()
mock_action_status.SUCCESS = "SUCCESS"
mock_action_status.FAILURE = "FAILURE"
sys.modules['coinbase_agentkit.types'].ActionStatus = mock_action_status

# Create ActionResult mock
class MockActionResult:
    def __init__(self, status="SUCCESS", transaction_hash="0xtest", message="Test successful", amount_out="1000"):
        self.status = status
        self.transaction_hash = transaction_hash
        self.message = message
        self.amount_out = amount_out

sys.modules['coinbase_agentkit.types'].ActionResult = MockActionResult

# Now import the swap tool
from horus.tools.swap import SwapTool

# Sample test data
SAMPLE_TOKENS_CONFIG = {
    "tokens": [
        {
            "symbol": "USDC",
            "name": "USD Coin",
            "chains": {
                "84532": "0xf175520c52418dfe19c8098071a252da48cd1c19",
                "1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
            }
        },
        {
            "symbol": "ETH",
            "name": "Ethereum",
            "chains": {
                "84532": "0x4200000000000000000000000000000000000006",
                "1": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
            }
        },
        {
            "symbol": "WETH",
            "name": "Wrapped Ethereum",
            "chains": {
                "84532": "0x4200000000000000000000000000000000000006",
                "1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
            }
        }
    ]
}

SAMPLE_PROTOCOLS_CONFIG = {
    "protocols": [
        {
            "name": "UniswapV3",
            "chains": {
                "84532": {
                    "swapRouter": "0xbe330043dbf77f92be10e3e3499d8da189d638cb"
                },
                "1": {
                    "swapRouter": "0xe592427a0aece92de3edee1f18e0157c05861564"
                }
            }
        },
        {
            "name": "SushiSwap",
            "chains": {
                "84532": {
                    "router": "0x1b02da8cb0d097eb8d57a175b88c7d8b47997506"
                }
            }
        }
    ]
}

SAMPLE_DEPENDENCY_GRAPH = {
    "nodes": [
        {
            "symbol": "USDC",
            "chainId": "84532",
            "priceFeed": "0x1234567890abcdef1234567890abcdef12345678"
        },
        {
            "symbol": "ETH",
            "chainId": "84532",
            "priceFeed": "0x1234567890abcdef1234567890abcdef12345678"
        }
    ]
}


class TestSwapTool(unittest.TestCase):
    """Test case for the SwapTool."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock for CdpActionProvider
        self.mock_action_provider = MagicMock()
        self.mock_wallet_provider = MagicMock()
        
        # Configure the mock to return a success result
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.transaction_hash = "0x1234567890abcdef"
        mock_result.message = "Swap successful"
        mock_result.amount_out = "1850.0"  # Example: 1 ETH -> 1850 USDC
        self.mock_action_provider.execute_swap.return_value = mock_result
        
        # Configure wallet provider to return a default account
        self.mock_wallet_provider.get_default_account.return_value = "0xDefaultAccount"
        
        # Create patches
        self.action_provider_patcher = patch('horus.tools.swap.CdpActionProvider')
        self.wallet_provider_patcher = patch('horus.tools.swap.CdpWalletProvider')
        
        # Start the patches
        mock_action_provider_class = self.action_provider_patcher.start()
        mock_wallet_provider_class = self.wallet_provider_patcher.start()
        
        # Configure the mock classes to return our mocks
        mock_action_provider_class.return_value = self.mock_action_provider
        mock_wallet_provider_class.return_value = self.mock_wallet_provider
        
        # Mark AgentKit as available
        with patch('horus.tools.swap.AGENTKIT_AVAILABLE', True):
            self.swap_tool = SwapTool(
                SAMPLE_TOKENS_CONFIG,
                SAMPLE_PROTOCOLS_CONFIG,
                SAMPLE_DEPENDENCY_GRAPH
            )
        
        # Set the mocks directly on the instance
        self.swap_tool._cdp_action_provider = self.mock_action_provider
        self.swap_tool._cdp_wallet_provider = self.mock_wallet_provider
    
    def tearDown(self):
        """Clean up after the test."""
        # Stop the patches
        self.action_provider_patcher.stop()
        self.wallet_provider_patcher.stop()
    
    def test_get_token_address(self):
        """Test retrieving token addresses."""
        # Update the token config to use the expected format
        self.swap_tool.tokens_config = {
            "tokens": [
                {
                    "symbol": "USDC",
                    "chains": {"84532": "0xf175520c52418dfe19c8098071a252da48cd1c19"}
                },
                {
                    "symbol": "WETH",
                    "chains": {"84532": "0x4200000000000000000000000000000000000006"}
                }
            ]
        }
        
        # Test getting a token address for a known token/chain
        address = self.swap_tool.get_token_address("USDC", "84532")
        self.assertEqual(address, "0xf175520c52418dfe19c8098071a252da48cd1c19")
        
        # Test getting a token address for a non-existent token
        address = self.swap_tool.get_token_address("NONEXISTENT", "84532")
        self.assertIsNone(address)
        
        # Test getting a token address for a known token but non-existent chain
        address = self.swap_tool.get_token_address("USDC", "999")
        self.assertIsNone(address)
        
        # Test token address caching
        # First call should cache the result
        address1 = self.swap_tool.get_token_address("WETH", "84532")
        self.assertEqual(address1, "0x4200000000000000000000000000000000000006")
        
        # Modify the cache to test that subsequent calls use the cached value
        self.swap_tool._token_address_cache["weth:84532"] = "0xmodified"
        address2 = self.swap_tool.get_token_address("WETH", "84532")
        self.assertEqual(address2, "0xmodified")
    
    def test_get_dex_router(self):
        """Test retrieving DEX router addresses."""
        # Test getting a router address for a known DEX/chain
        router = self.swap_tool.get_dex_router("UniswapV3", "84532")
        self.assertEqual(router, "0xbe330043dbf77f92be10e3e3499d8da189d638cb")
        
        # Test getting a router for a non-existent DEX
        router = self.swap_tool.get_dex_router("NonexistentDEX", "84532")
        self.assertIsNone(router)
        
        # Test getting a router for a known DEX but non-existent chain
        router = self.swap_tool.get_dex_router("UniswapV3", "999")
        self.assertIsNone(router)
        
        # Test case insensitivity for DEX name
        router = self.swap_tool.get_dex_router("uniswapv3", "84532")
        self.assertEqual(router, "0xbe330043dbf77f92be10e3e3499d8da189d638cb")
        
        # Test different router key (router instead of swapRouter)
        router = self.swap_tool.get_dex_router("SushiSwap", "84532")
        self.assertEqual(router, "0x1b02da8cb0d097eb8d57a175b88c7d8b47997506")
    
    def test_get_default_dex(self):
        """Test getting default DEX for different chains."""
        self.assertEqual(self.swap_tool.get_default_dex("1"), "UniswapV3")  # Ethereum
        self.assertEqual(self.swap_tool.get_default_dex("84532"), "UniswapV3")  # Base
        self.assertEqual(self.swap_tool.get_default_dex("137"), "QuickSwap")  # Polygon
        self.assertEqual(self.swap_tool.get_default_dex("999"), "UniswapV3")  # Unknown chain defaults to Uniswap
    
    def test_estimate_output_amount(self):
        """Test output amount estimation."""
        # Test ETH to USDC conversion
        output = self.swap_tool.estimate_output_amount("ETH", "USDC", "1.0", "84532")
        # 1 ETH * 1800 * 0.98 (slippage) = 1764
        self.assertAlmostEqual(float(output), 1764.0)
        
        # Test USDC to ETH conversion
        output = self.swap_tool.estimate_output_amount("USDC", "ETH", "1800.0", "84532")
        # 1800 USDC * (1/1800) * 0.98 = 0.98
        self.assertAlmostEqual(float(output), 0.98, places=2)
        
        # Test a token pair that isn't directly defined
        output = self.swap_tool.estimate_output_amount("TOKEN1", "TOKEN2", "100", "84532")
        # Default to 1:1 ratio for unknown pairs
        self.assertAlmostEqual(float(output), 98.0)  # 100 * 1 * 0.98
        
        # Test with invalid amount
        output = self.swap_tool.estimate_output_amount("ETH", "USDC", "invalid", "84532")
        self.assertEqual(output, "0")
    
    def test_execute_swap_with_agentkit(self):
        """Test executing a swap with AgentKit."""
        result = self.swap_tool.execute_swap_with_agentkit(
            token_in_address="0x4200000000000000000000000000000000000006",  # ETH on Base
            token_out_address="0xf175520c52418dfe19c8098071a252da48cd1c19",  # USDC on Base
            amount_in="1.0",
            min_amount_out="1764.0",
            router_address="0xbe330043dbf77f92be10e3e3499d8da189d638cb",  # UniswapV3 router on Base
            chain_id="84532",
            slippage=0.5
        )
        
        # Check that the result has the expected structure
        self.assertTrue(result["success"])
        self.assertEqual(result["transaction_hash"], "0x1234567890abcdef")
        self.assertEqual(result["message"], "Swap successful")
        self.assertEqual(result["amount_in"], "1.0")
        self.assertEqual(result["amount_out"], "1850.0")
        
        # Check that the action provider was called with correct parameters
        self.mock_action_provider.execute_swap.assert_called_once_with(
            chain_id="84532",
            account="0xDefaultAccount",
            token_in="0x4200000000000000000000000000000000000006",
            token_out="0xf175520c52418dfe19c8098071a252da48cd1c19",
            amount_in="1.0",
            slippage_percentage=0.5,
            fee_tier=3000
        )
    
    def test_execute_success(self):
        """Test the main execute method for a successful swap."""
        # Update the token config to use the expected format
        self.swap_tool.tokens_config = {
            "tokens": [
                {
                    "symbol": "USDC",
                    "chains": {"84532": "0xf175520c52418dfe19c8098071a252da48cd1c19"}
                },
                {
                    "symbol": "ETH",
                    "chains": {"84532": "0x4200000000000000000000000000000000000006"}
                }
            ]
        }
        
        parameters = {
            "token_in": "ETH",
            "token_out": "USDC",
            "amount_in": "1.0",
            "chain_id": "84532"
        }
        
        result = self.swap_tool.execute(parameters)
        
        # Check that the result contains the expected success message
        self.assertIn("Successfully swapped 1.0 ETH", result)
        self.assertIn("1850.0 USDC", result)
        
        # Verify the action provider was called correctly
        self.mock_action_provider.execute_swap.assert_called_once()
    
    def test_execute_missing_parameters(self):
        """Test execute with missing required parameters."""
        # Missing token_in
        parameters1 = {
            "token_out": "USDC",
            "amount_in": "1.0",
            "chain_id": "84532"
        }
        result1 = self.swap_tool.execute(parameters1)
        self.assertIn("Error: Missing required parameters", result1)
        
        # Missing token_out
        parameters2 = {
            "token_in": "ETH",
            "amount_in": "1.0",
            "chain_id": "84532"
        }
        result2 = self.swap_tool.execute(parameters2)
        self.assertIn("Error: Missing required parameters", result2)
    
    def test_execute_unknown_token(self):
        """Test execute with unknown tokens."""
        # Update the token config to use the expected format
        self.swap_tool.tokens_config = {
            "tokens": [
                {
                    "symbol": "USDC",
                    "chains": {"84532": "0xf175520c52418dfe19c8098071a252da48cd1c19"}
                },
                {
                    "symbol": "ETH",
                    "chains": {"84532": "0x4200000000000000000000000000000000000006"}
                }
            ]
        }
        
        parameters = {
            "token_in": "NONEXISTENT",
            "token_out": "USDC",
            "amount_in": "1.0",
            "chain_id": "84532"
        }
        result = self.swap_tool.execute(parameters)
        self.assertIn("Error: Could not find address for token NONEXISTENT", result)
    
    def test_execute_unknown_dex(self):
        """Test execute with an unknown DEX."""
        # Update the token config to use the expected format
        self.swap_tool.tokens_config = {
            "tokens": [
                {
                    "symbol": "USDC",
                    "chains": {"84532": "0xf175520c52418dfe19c8098071a252da48cd1c19"}
                },
                {
                    "symbol": "ETH",
                    "chains": {"84532": "0x4200000000000000000000000000000000000006"}
                }
            ]
        }
        
        parameters = {
            "token_in": "ETH",
            "token_out": "USDC",
            "amount_in": "1.0",
            "chain_id": "84532",
            "dex": "NonexistentDEX"
        }
        result = self.swap_tool.execute(parameters)
        self.assertIn("Error: Could not find router address for NonexistentDEX", result)
    
    def test_simulate_mode(self):
        """Test swapping in simulation mode when AgentKit is not available."""
        # Create a new instance with AGENTKIT_AVAILABLE set to False
        with patch('horus.tools.swap.AGENTKIT_AVAILABLE', False):
            swap_tool = SwapTool(
                SAMPLE_TOKENS_CONFIG,
                SAMPLE_PROTOCOLS_CONFIG,
                SAMPLE_DEPENDENCY_GRAPH
            )
            
            # Execute a swap that should be simulated
            result = swap_tool.execute_swap_with_agentkit(
                token_in_address="0x4200000000000000000000000000000000000006",
                token_out_address="0xf175520c52418dfe19c8098071a252da48cd1c19",
                amount_in="1.0",
                min_amount_out="1764.0",
                router_address="0xbe330043dbf77f92be10e3e3499d8da189d638cb",
                chain_id="84532"
            )
            
            # Check that we got a simulated response
            self.assertTrue(result["success"])
            self.assertTrue(result["transaction_hash"].startswith("0x"))
            self.assertIn("Simulated swap", result["message"])
            self.assertTrue("testnet_simulation" in result)
    
    def test_execute_swap_with_agentkit_error(self):
        """Test error handling in execute_swap_with_agentkit."""
        # Configure the mock to raise an exception
        self.mock_action_provider.execute_swap.side_effect = Exception("Test error")
        
        result = self.swap_tool.execute_swap_with_agentkit(
            token_in_address="0x4200000000000000000000000000000000000006",
            token_out_address="0xf175520c52418dfe19c8098071a252da48cd1c19",
            amount_in="1.0",
            min_amount_out="1764.0",
            router_address="0xbe330043dbf77f92be10e3e3499d8da189d638cb",
            chain_id="84532"
        )
        
        # Check that the error was handled correctly
        self.assertFalse(result["success"])
        self.assertIsNone(result["transaction_hash"])
        self.assertEqual(result["message"], "Error executing swap with AgentKit: Test error")
    
    def test_execute_swap_failure(self):
        """Test execute when the swap fails."""
        # Update the token config to use the expected format
        self.swap_tool.tokens_config = {
            "tokens": [
                {
                    "symbol": "USDC",
                    "chains": {"84532": "0xf175520c52418dfe19c8098071a252da48cd1c19"}
                },
                {
                    "symbol": "ETH",
                    "chains": {"84532": "0x4200000000000000000000000000000000000006"}
                }
            ]
        }
        
        # Configure the mock to return a failure result
        mock_failure_result = MagicMock()
        mock_failure_result.status = "FAILURE"
        mock_failure_result.transaction_hash = None
        mock_failure_result.message = "Swap failed due to insufficient liquidity"
        self.mock_action_provider.execute_swap.return_value = mock_failure_result
        
        parameters = {
            "token_in": "ETH",
            "token_out": "USDC",
            "amount_in": "1.0",
            "chain_id": "84532"
        }
        
        result = self.swap_tool.execute(parameters)
        
        # Check that the result contains the expected failure message
        self.assertIn("Error swapping tokens", result)
        self.assertIn("Swap failed due to insufficient liquidity", result)
    
    def test_callable_interface(self):
        """Test the callable interface of SwapTool."""
        # Mock the execute method
        self.swap_tool.execute = MagicMock(return_value="Executed successfully")
        
        # Call the instance directly
        parameters = {"token_in": "ETH", "token_out": "USDC"}
        result = self.swap_tool(parameters)
        
        # Check that execute was called with the parameters
        self.swap_tool.execute.assert_called_once_with(parameters)
        self.assertEqual(result, "Executed successfully")


if __name__ == "__main__":
    unittest.main() 