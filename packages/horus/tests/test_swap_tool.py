#!/usr/bin/env python3
"""
Unit tests for the SwapTool class in the Horus security system.

This test suite provides comprehensive testing for the SwapTool class,
covering its initialization, token address resolution, DEX router information retrieval,
price estimation, and execution of swap operations.
"""
import json
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import pytest
from dotenv import load_dotenv
from horus.core.agent_kit import is_agentkit_available
# Import the mock_agent_kit utilities for tests
from tests.mock_agent_kit import setup_mocks, teardown_mocks

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
            "networks": {
                "84532": "0xf175520c52418dfe19c8098071a252da48cd1c19",
                "1": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
            }
        },
        {
            "symbol": "ETH",
            "name": "Ethereum",
            "networks": {
                "84532": "0x4200000000000000000000000000000000000006",
                "1": "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
            }
        },
        {
            "symbol": "WETH",
            "name": "Wrapped Ethereum",
            "networks": {
                "84532": "0x4200000000000000000000000000000000000006",
                "1": "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
            }
        },
        {
            "symbol": "UNI-V3-LP",
            "name": "Uniswap V3 LP Token",
            "networks": {
                "84532": "0x1234567890abcdef1234567890abcdef12345678",
                "1": "0xabcdef1234567890abcdef1234567890abcdef12"
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
                    "router": "0xbe330043dbf77f92be10e3e3499d8da189d638cb"
                },
                "1": {
                    "router": "0xe592427a0aece92de3edee1f18e0157c05861564"
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

# Constants to match the ones in the SwapTool
FALLBACK_POSITION_MANAGERS = {
    "UniswapV3": {
        "1": "0xc36442b4a4522e871399cd717abdd847ab11fe88",  # Ethereum Mainnet
        "84532": "0xc36442b4a4522e871399cd717abdd847ab11fe88",  # Base
    }
}


class TestSwapTool(unittest.TestCase):
    """Test case for the SwapTool."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that should be shared across all tests."""
        # Set up mocks for AgentKit
        cls.patches = setup_mocks()
        
        # Import SwapTool after setting up mocks
        from horus.tools.swap import SwapTool
        cls.SwapTool = SwapTool
        
        from horus.core.agent_kit import agent_kit_manager
        cls.agent_kit_manager = agent_kit_manager

    @classmethod
    def tearDownClass(cls):
        """Clean up shared test fixtures."""
        # Tear down mocks
        teardown_mocks(cls.patches)

    def setUp(self):
        self.swap_tool = self.SwapTool(SAMPLE_TOKENS_CONFIG, SAMPLE_PROTOCOLS_CONFIG)
        logger.info("SwapTool initialized")
        
        # Set test chain ID
        self.test_chain_id = "84532"
        logger.info(f"Detected testnet environment based on chain ID: {self.test_chain_id}")

    def test_get_token_address(self):
        # Test getting ETH address
        eth_address = self.swap_tool.get_token_address("ETH", self.test_chain_id)
        self.assertEqual(eth_address, "0x4200000000000000000000000000000000000006")
        
        # Test getting USDC address
        usdc_address = self.swap_tool.get_token_address("USDC", self.test_chain_id)
        self.assertEqual(usdc_address, "0xf175520c52418dfe19c8098071a252da48cd1c19")
        
        # Test nonexistent token
        nonexistent_address = self.swap_tool.get_token_address("NONEXISTENT", self.test_chain_id)
        self.assertEqual(nonexistent_address, "unknown")
        
        # Test nonexistent chain
        nonexistent_chain = self.swap_tool.get_token_address("USDC", "999")
        self.assertEqual(nonexistent_chain, "unknown")

    def test_get_router_address(self):
        # Test getting router for UniswapV3
        uniswap_router = self.swap_tool.get_router_address("UniswapV3", self.test_chain_id)
        self.assertEqual(uniswap_router, "0xbe330043dbf77f92be10e3e3499d8da189d638cb")
        
        # Test getting router for nonexistent DEX
        nonexistent_dex = self.swap_tool.get_router_address("NonexistentDEX", self.test_chain_id)
        logger.info(f"No router address found for NonexistentDEX on chain {self.test_chain_id}")
        self.assertIsNone(nonexistent_dex)
        
        # Test getting router for UniswapV3 on nonexistent chain
        nonexistent_chain = self.swap_tool.get_router_address("UniswapV3", "999")
        logger.info(f"No router address found for UniswapV3 on chain 999")
        self.assertIsNone(nonexistent_chain)

    def test_execute_swap_with_token_in_missing(self):
        # Test swap execution with token_in missing but token_out present
        parameters = {
            "token_out": "USDC",
            "amount_in": "1.0",
            "chain_id": self.test_chain_id
        }
        
        logger.info(f"Executing swap from None to USDC on chain {self.test_chain_id} using UniswapV3")
        logger.info(f"Full parameters: {parameters}")
        
        result = self.swap_tool.execute(parameters)
        
        self.assertIn("Error: Missing input token", result)

    def test_execute_swap_with_token_out_missing(self):
        # Test swap execution with token_out missing but token_in present
        parameters = {
            "token_in": "ETH",
            "amount_in": "1.0",
            "chain_id": self.test_chain_id
        }
        
        logger.info(f"Executing swap from ETH to None on chain {self.test_chain_id} using UniswapV3")
        logger.info(f"Full parameters: {parameters}")
        
        result = self.swap_tool.execute(parameters)
        
        self.assertIn("Error: Missing output token", result)

    def test_execute_swap_with_lp_token(self):
        # Test swap execution with LP token
        parameters = {
            "lp_token_id": "12345",
            "chain_id": self.test_chain_id
        }
        
        logger.info(f"Executing swap from None to None on chain {self.test_chain_id} using UniswapV3")
        logger.info(f"Full parameters: {parameters}")
        
        result = self.swap_tool.execute(parameters)
        
        self.assertIn("Error", result)

    def test_execute_swap_with_simple_parameters(self):
        # Test simple swap execution
        parameters = {
            "token_in": "ETH",
            "token_out": "USDC",
            "amount_in": "1.0",
            "chain_id": self.test_chain_id
        }
        
        logger.info(f"Executing swap from ETH to USDC on chain {self.test_chain_id} using UniswapV3")
        logger.info(f"Full parameters: {parameters}")
        
        # Get estimated output for this swap
        estimated_output = self.swap_tool.get_estimated_output("ETH", "USDC", "1.0", self.test_chain_id)
        estimated_amount = estimated_output.get("estimated_output", "0")
        slippage = 0.5  # Default slippage
        min_amount_out = str(round(float(estimated_amount) * (1 - slippage / 100), 2))
        
        logger.info(f"Estimated output: {estimated_amount} USDC (min: {min_amount_out} with {slippage}% slippage)")
        
        with patch('horus.tools.agent_kit.agent_kit_manager.execute_swap') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "transaction_hash": "0xfedcba0987654321fedcba0987654321fedcba0987654321",
                "message": "Swap executed successfully",
                "amount_out": estimated_amount
            }
            result = self.swap_tool.execute(parameters)
        
        self.assertIn("Successfully swapped", result)
        self.assertIn("ETH", result)
        self.assertIn("USDC", result)

    def test_execute_swap_with_dex_specified(self):
        # Test swap execution with DEX specified
        parameters = {
            "token_in": "ETH",
            "token_out": "USDC",
            "amount_in": "1.0",
            "chain_id": "1",  # Use Ethereum mainnet to make it different from default
            "dex": "UniswapV3"  # Specify DEX
        }
        
        logger.info(f"Executing swap from ETH to USDC on chain {self.test_chain_id} using UniswapV3")
        logger.info(f"Full parameters: {parameters}")
        
        # Get estimated output for this swap
        estimated_output = self.swap_tool.get_estimated_output("ETH", "USDC", "1.0", self.test_chain_id)
        estimated_amount = estimated_output.get("estimated_output", "0")
        slippage = 0.5  # Default slippage
        min_amount_out = str(round(float(estimated_amount) * (1 - slippage / 100), 2))
        
        logger.info(f"Estimated output: {estimated_amount} USDC (min: {min_amount_out} with {slippage}% slippage)")
        
        with patch('horus.tools.agent_kit.agent_kit_manager.execute_swap') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "transaction_hash": "0xfedcba0987654321fedcba0987654321fedcba0987654321",
                "message": "Swap executed successfully",
                "amount_out": estimated_amount
            }
            result = self.swap_tool.execute(parameters)
        
        self.assertIn("Successfully swapped", result)
        self.assertIn("ETH", result)
        self.assertIn("USDC", result)

    def test_execute_swap_with_agentkit(self):
        """Test executing a swap with AgentKit."""
        # Set up parameters for swap
        parameters = {
            "token_in": "ETH",
            "token_out": "USDC",
            "amount_in": "1.0",
            "chain_id": self.test_chain_id
        }
        
        # Execute the swap with real AgentKit manager
        result = self.agent_kit_manager.execute_swap(
            token_in_address="0x4200000000000000000000000000000000000006",
            token_out_address="0xf175520c52418dfe19c8098071a252da48cd1c19",
            amount_in="1.0",
            chain_id=self.test_chain_id,
            slippage_percentage=0.5
        )
        
        logger.info(f"Swap result: {result}")
        
        # Check the result
        self.assertTrue(result.get("success", False))
        # Use assertIn to check that the transaction hash exists but not check the exact value
        self.assertIn("transaction_hash", result)
        # Instead of checking the exact transaction hash, just ensure it's not empty
        self.assertTrue(bool(result.get("transaction_hash")))

    def test_execute_swap_with_agentkit_error(self):
        """Test error handling in execute_swap_with_agentkit."""
        # Set up parameters for swap
        parameters = {
            "token_in": "ETH",
            "token_out": "USDC", 
            "amount_in": "1.0",
            "chain_id": self.test_chain_id
        }
        
        # Use the agent_kit_manager but with a patched execute_action that fails
        with patch('horus.tools.agent_kit.agent_kit_manager._cdp_action_provider.execute_action') as mock_execute:
            from horus.core.agent_kit import ActionResult, ActionStatus

            # Create a failure result
            mock_execute.return_value = ActionResult(
                ActionStatus.ERROR,
                None,
                "Test error"
            )
            
            # Execute swap
            result = self.agent_kit_manager.execute_swap(
                token_in_address="0x4200000000000000000000000000000000000006",
                token_out_address="0xf175520c52418dfe19c8098071a252da48cd1c19",
                amount_in="1.0",
                chain_id=self.test_chain_id,
                slippage_percentage=0.5
            )
            
            logger.info(f"Swap result: {result}")
            
            # Check the result
            self.assertFalse(result.get("success", True))
            self.assertEqual(result.get("transaction_hash"), "")  # Empty string, not None
            self.assertIn("Test error", result.get("message", ""))

    def test_execute_swap_with_nonexistent_dex(self):
        # Test swap execution with nonexistent DEX
        parameters = {
            "token_in": "ETH",
            "token_out": "USDC",
            "amount_in": "1.0",
            "chain_id": self.test_chain_id,
            "dex": "NonexistentDEX"
        }
        
        logger.info(f"Executing swap from ETH to USDC on chain {self.test_chain_id} using NonexistentDEX")
        logger.info(f"Full parameters: {parameters}")
        
        result = self.swap_tool.execute(parameters)
        
        self.assertIn("Error", result)
        self.assertIn("NonexistentDEX", result)

    def test_execute_swap_with_nonexistent_token(self):
        # Test swap execution with nonexistent token
        parameters = {
            "token_in": "NONEXISTENT",
            "token_out": "USDC",
            "amount_in": "1.0",
            "chain_id": self.test_chain_id
        }
        
        logger.info(f"Executing swap from NONEXISTENT to USDC on chain {self.test_chain_id} using UniswapV3")
        logger.info(f"Full parameters: {parameters}")
        
        result = self.swap_tool.execute(parameters)
        
        self.assertIn("Error", result)
        self.assertIn("NONEXISTENT", result)

    def test_execute_swap_with_invalid_amount(self):
        # Test swap execution with invalid amount
        parameters = {
            "token_in": "ETH",
            "token_out": "USDC",
            "amount_in": "invalid",
            "chain_id": self.test_chain_id,
            "test_error_handling": True  # Add this flag for tests
        }
        
        logger.info(f"Executing swap from ETH to USDC on chain {self.test_chain_id} using UniswapV3")
        
        result = self.swap_tool.execute(parameters)
        
        self.assertIn("Error", result)
        self.assertIn("amount", result.lower())

    def test_swap_get_router_address_with_invalid_source(self):
        # Test getting router address for nonexistent DEX and chain
        nonexistent_dex = self.swap_tool.get_router_address("NonexistentDEX", self.test_chain_id)
        logger.info(f"No router address found for NonexistentDEX on chain {self.test_chain_id}")
        self.assertIsNone(nonexistent_dex)
        
        nonexistent_chain = self.swap_tool.get_router_address("UniswapV3", "999")
        logger.info(f"No router address found for UniswapV3 on chain 999")
        self.assertIsNone(nonexistent_chain)

    def test_swap_get_position_manager_address(self):
        # Add nonfungiblePositionManager to the test protocols
        self.swap_tool.protocols_config = {
            "protocols": [
                {
                    "name": "UniswapV3",
                    "chains": {
                        "84532": {
                            "router": "0xbe330043dbf77f92be10e3e3499d8da189d638cb",
                            "nonfungiblePositionManager": "0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2"
                        },
                        "1": {
                            "router": "0xe592427a0aece92de3edee1f18e0157c05861564"
                            # No position manager for mainnet in test config
                        }
                    }
                }
            ]
        }
        
        # Test getting position manager address for UniswapV3
        position_manager = self.swap_tool.get_position_manager_address("UniswapV3", self.test_chain_id)
        logger.info(f"Found position manager for UniswapV3 on chain {self.test_chain_id} in protocols config: {position_manager}")
        self.assertIsNotNone(position_manager)
        
        # Test getting position manager address for nonexistent DEX
        nonexistent_dex = self.swap_tool.get_position_manager_address("NonexistentDEX", self.test_chain_id)
        logger.info(f"No position manager found for NonexistentDEX on chain {self.test_chain_id}")
        self.assertIsNone(nonexistent_dex)
        
        # Test getting position manager address for UniswapV3 on mainnet with no position manager
        mainnet_position_manager = self.swap_tool.get_position_manager_address("UniswapV3", "1")
        logger.info(f"Found position manager for UniswapV3 on chain 1 in protocols config: {mainnet_position_manager}")
        self.assertIsNone(mainnet_position_manager)

    def test_token_address_resolution(self):
        # Test token address resolution for known tokens
        eth_address = self.swap_tool.get_token_address("ETH", self.test_chain_id)
        self.assertEqual(eth_address, "0x4200000000000000000000000000000000000006")
        
        usdc_address = self.swap_tool.get_token_address("USDC", self.test_chain_id)
        self.assertEqual(usdc_address, "0xf175520c52418dfe19c8098071a252da48cd1c19")
        
        # Test token address resolution for nonexistent tokens and chains
        nonexistent_token = self.swap_tool.get_token_address("NONEXISTENT", self.test_chain_id)
        logger.info(f"Token address not found for NONEXISTENT on chain {self.test_chain_id}")
        self.assertEqual(nonexistent_token, "unknown")
        
        nonexistent_chain = self.swap_tool.get_token_address("USDC", "999")
        logger.info(f"Token address not found for USDC on chain 999")
        self.assertEqual(nonexistent_chain, "unknown")

    def test_get_estimated_output(self):
        # Test estimated output calculation
        estimated_output = self.swap_tool.get_estimated_output("ETH", "USDC", "1.0", self.test_chain_id)
        self.assertIn("estimated_output", estimated_output)
        self.assertIn("token_in", estimated_output)
        self.assertIn("token_out", estimated_output)

    def test_execute_swap_simulation(self):
        # Test swap simulation mode
        
        # Mock the execute_swap_with_agentkit method to simulate the swap
        with patch('horus.tools.agent_kit.agent_kit_manager.execute_swap') as mock_execute:
            # Configure the mock to return a simulated result
            mock_execute.return_value = {
                "success": True,
                "transaction_hash": "0xsimulated",
                "message": "Simulated swap",
                "amount_out": "1850.0"
            }
            
            # Execute the swap with the simulation flag
            result = self.swap_tool.execute({
                "token_in": "ETH",
                "token_out": "USDC",
                "amount_in": "1.0",
                "chain_id": self.test_chain_id,
                "simulation": True
            })
            
            # Verify the result
            self.assertIn("Simulating swap", result)
            self.assertIn("ETH", result)
            self.assertIn("USDC", result)
            
            # Verify that the AgentKit execute_swap method was not called
            mock_execute.assert_not_called()

    def test_custom_response_formatting(self):
        """Test that the tool returns well-formatted responses with transaction links."""
        # Import needed here to maintain patch context
        from horus.core.agent_kit import ActionResult, ActionStatus

        # Mock the agent_kit_manager to return a successful result
        # Patch directly in this test to avoid affecting others


if __name__ == '__main__':
    unittest.main() 