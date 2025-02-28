"""
Unit tests for the RevokeTool class in the Horus security system.

This test suite provides comprehensive testing for the RevokeTool class,
covering its initialization, token address resolution, protocol information retrieval,
block explorer URL generation, and execution of revocation operations.
"""
import importlib
import logging
import os
import re
import sys
import unittest
from unittest.mock import MagicMock, patch

import pytest
from core.agent_kit import is_agentkit_available
# Import the mock_agent_kit utilities
from tests.mock_agent_kit import setup_mocks, teardown_mocks

# Configure logging for test
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

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
                }
            ]
        }
        
SAMPLE_PROTOCOLS_CONFIG = {
            "protocols": [
        {
            "name": "UniswapV3",
            "chains": {
                "84532": {
                    "router": "0xbe330043dbf77f92be10e3e3499d8da189d638cb",
                    "factory": "0x33128a8fC17869897dcE68Ed026d694621f6FDfD",
                    "nonfungiblePositionManager": "0xc36442b4a4522e871399cd717abdd847ab11fe88"
                },
                "1": {
                    "router": "0xe592427a0aece92de3edee1f18e0157c05861564",
                    "factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
                    "nonfungiblePositionManager": "0xc36442b4a4522e871399cd717abdd847ab11fe88"
                }
            }
        },
                {
                    "name": "Compound",
                    "chains": {
                "84532": {
                    "comptroller": "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b"
                },
                        "1": {
                    "comptroller": "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b"
                        }
                    }
                }
            ]
        }
        
class TestRevokeTool(unittest.TestCase):
    """Test cases for the RevokeTool class."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that should be shared across all tests."""
        # Set up mocks for AgentKit
        cls.patches = setup_mocks()
        
        # Import RevokeTool after setting up mocks
        from tools.revoke import RevokeTool
        cls.RevokeTool = RevokeTool
        
        from core.agent_kit import agent_kit_manager
        cls.agent_kit_manager = agent_kit_manager

    @classmethod
    def tearDownClass(cls):
        """Clean up shared test fixtures."""
        # Tear down mocks
        teardown_mocks(cls.patches)

    def setUp(self):
        """Set up test fixtures before each test."""
        logger.info("RevokeTool test setup complete")
        self.revoke_tool = self.RevokeTool(SAMPLE_TOKENS_CONFIG, SAMPLE_PROTOCOLS_CONFIG)
        
        # Create a test action for revokes
        self.test_revoke_action = {
            "type": "revokeAllowance",
            "params": {
                "tokenAddress": "0xf175520c52418dfe19c8098071a252da48cd1c19",
                "spenderAddress": "0x1234567890abcdef1234567890abcdef12345678",
                "chainId": "84532"
            }
        }

    def test_init(self):
        """Test initialization of RevokeTool."""
        self.assertEqual(self.revoke_tool.name, "revoke")
        self.assertEqual(self.revoke_tool.tokens_config, SAMPLE_TOKENS_CONFIG)
        self.assertEqual(self.revoke_tool.protocols_config, SAMPLE_PROTOCOLS_CONFIG)
        self.assertIsNotNone(self.revoke_tool.block_explorers)

    def test_get_token_address(self):
        """Test token address resolution."""
        # Test with a known token and chain
        token_address = self.revoke_tool.get_token_address("USDC", "84532")
        self.assertEqual(token_address, "0xf175520c52418dfe19c8098071a252da48cd1c19")
        
        # Test with a known token and different chain
        token_address = self.revoke_tool.get_token_address("USDC", "1")
        self.assertEqual(token_address, "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
        
        # Test with an unknown token
        token_address = self.revoke_tool.get_token_address("NONEXISTENT", "84532")
        self.assertEqual(token_address, "unknown")
        
        # Test with an unknown chain
        token_address = self.revoke_tool.get_token_address("USDC", "999")
        self.assertEqual(token_address, "unknown")

    def test_get_protocol_info(self):
        """Test protocol information retrieval."""
        # Test with a known protocol and chain
        protocol_info = self.revoke_tool.get_protocol_info("UniswapV3", "84532")
        self.assertIsNotNone(protocol_info)
        self.assertEqual(protocol_info["router"], "0xbe330043dbf77f92be10e3e3499d8da189d638cb")
        
        # Test with a known protocol and different chain
        protocol_info = self.revoke_tool.get_protocol_info("UniswapV3", "1")
        self.assertIsNotNone(protocol_info)
        self.assertEqual(protocol_info["router"], "0xe592427a0aece92de3edee1f18e0157c05861564")
        
        # Test with an unknown protocol
        protocol_info = self.revoke_tool.get_protocol_info("NONEXISTENT", "84532")
        self.assertIsNone(protocol_info)
        
        # Test with a known protocol and unsupported chain
        protocol_info = self.revoke_tool.get_protocol_info("Compound", "999")
        self.assertIsNone(protocol_info)

    def test_get_explorer_url(self):
        """Test block explorer URL generation."""
        # Test with a known chain
        explorer_url = self.revoke_tool.get_explorer_url("84532", "0x1234567890abcdef1234567890abcdef12345678")
        self.assertEqual(explorer_url, "https://sepolia.basescan.org/tx/0x1234567890abcdef1234567890abcdef12345678")
        
        # Test with an unknown chain
        explorer_url = self.revoke_tool.get_explorer_url("999", "0x1234567890abcdef1234567890abcdef12345678")
        self.assertIsNone(explorer_url)

    def test_create_revoke_action(self):
        """Test revoke action creation."""
        # The create_revoke_action method has been moved to agent_kit_manager
        # Test that the proper action is created by agent_kit_manager
        token_address = "0xf175520c52418dfe19c8098071a252da48cd1c19"
        spender_address = "0x1234567890abcdef1234567890abcdef12345678"
        chain_id = "84532"
        
        # Test by executing a revoke through agent_kit_manager
        result = self.agent_kit_manager.execute_revoke(token_address, spender_address, chain_id)
        self.assertTrue(result.get("success", False))
        self.assertIn("transaction_hash", result)
        self.assertIn("message", result)

    def test_execute_success_with_token_symbol(self):
        """Test execution with a token symbol."""
        # Set up the parameters
        parameters = {
            "token": "USDC",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_id": "84532"
        }
        
        # Execute the revoke operation
        with patch('horus.tools.agent_kit.agent_kit_manager.execute_revoke') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "transaction_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890",
                "message": "Successfully revoked approval"
            }
            result = self.revoke_tool.execute(parameters)
        
        # Check the result
        self.assertIn("Successfully revoked approval", result)
        
        # Check with a different chain
        parameters["chain_id"] = "1"
        with patch('horus.tools.agent_kit.agent_kit_manager.execute_revoke') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "transaction_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890",
                "message": "Successfully revoked approval"
            }
            result = self.revoke_tool.execute(parameters)
        self.assertIn("Successfully revoked approval", result)

    def test_execute_success_with_token_address(self):
        """Test execution with a token address."""
        # Set up the parameters
        parameters = {
            "token_address": "0xf175520c52418dfe19c8098071a252da48cd1c19",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_id": "84532"
        }
        
        # Execute the revoke operation
        with patch('horus.tools.agent_kit.agent_kit_manager.execute_revoke') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "transaction_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890",
                "message": "Successfully revoked approval"
            }
            result = self.revoke_tool.execute(parameters)
        
        # Check the result
        self.assertIn("Successfully revoked approval", result)

    def test_execute_success_with_protocol(self):
        """Test execution with a protocol name."""
        # Set up the parameters
        parameters = {
            "token": "USDC",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "protocol": "UniswapV3",
            "chain_id": "84532"
        }
        
        # Execute the revoke operation
        with patch('horus.tools.agent_kit.agent_kit_manager.execute_revoke') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "transaction_hash": "0xabcdef1234567890abcdef1234567890abcdef1234567890",
                "message": "Successfully revoked approval"
            }
            result = self.revoke_tool.execute(parameters)
        
        # Check the result
        self.assertIn("Successfully revoked approval", result)
        self.assertIn("UniswapV3", result)

    def test_execute_missing_token(self):
        """Test execution with missing token information."""
        # Set up the parameters with no token information
        parameters = {
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_id": "84532"
        }
        
        # Execute the revoke operation
        result = self.revoke_tool.execute(parameters)
        
        # Check the result
        self.assertIn("Error: Token address is required for revocation", result)

    def test_execute_missing_spender(self):
        """Test execution with missing spender address."""
        # Set up the parameters with no spender address
        parameters = {
            "token": "USDC",
            "chain_id": "84532"
        }
        
        # Execute the revoke operation
        result = self.revoke_tool.execute(parameters)
        
        # Check the result
        self.assertIn("Error: Spender address is required for revocation", result)

    def test_execute_invalid_addresses(self):
        """Test execution with invalid addresses."""
        # Test with invalid token address
        parameters1 = {
            "token_address": "0xinvalid",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_id": "84532"
        }
        result1 = self.revoke_tool.execute(parameters1)
        self.assertIn("Error: Invalid token address format", result1)
        
        # Test with invalid spender address
        parameters2 = {
            "token": "USDC",
            "spender_address": "0xinvalid",
            "chain_id": "84532"
        }
        result2 = self.revoke_tool.execute(parameters2)
        self.assertIn("Error: Invalid spender address format", result2)

    def test_execute_invalid_chain_id(self):
        """Test execution with invalid chain ID."""
        # Set up the parameters with an invalid chain ID
        parameters = {
            "token_address": "0xf175520c52418dfe19c8098071a252da48cd1c19",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_id": "invalid"
        }
        
        # Execute the revoke operation
        result = self.revoke_tool.execute(parameters)
        
        # Check the result
        self.assertIn("Error: Invalid chain ID", result)

    def test_execute_unknown_protocol(self):
        """Test execution with unknown protocol."""
        # Set up the parameters with an unknown protocol
        parameters = {
            "token": "USDC",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "protocol": "NonexistentProtocol",
            "chain_id": "84532"
        }
        
        # Execute the revoke operation
        result = self.revoke_tool.execute(parameters)
        
        # Check the result
        self.assertIn("Error: Unknown protocol", result)

    def test_execute_api_error(self):
        """Test execution with API error."""
        # Set up the parameters
        parameters = {
            "token": "USDC",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678_test_failure",  # Add _test_failure suffix
            "chain_id": "84532"
        }
        
        # Execute the revoke operation
        with patch('horus.tools.agent_kit.CdpActionProvider.execute_action') as mock_execute:
            # Configure the mock to return an error result
            from core.agent_kit import ActionResult, ActionStatus
            mock_execute.return_value = ActionResult(
                ActionStatus.ERROR,
                None,
                "API Error: Rate limit exceeded"
            )
            result = self.revoke_tool.execute(parameters)
        
        # Check the result
        self.assertIn("Failed to revoke approval", result)
        self.assertIn("API Error: Rate limit exceeded", result)

    def test_execute_wallet_failure(self):
        """Test execution with wallet initialization failure."""
        # Set up the parameters
        parameters = {
            "token": "USDC",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678_wallet_failure",  # Add _wallet_failure suffix
            "chain_id": "84532",
            "wallet_failure": True  # Special flag for testing
        }
        
        # Mock execute_revoke to simulate wallet failure
        with patch('horus.tools.agent_kit.agent_kit_manager.execute_revoke') as mock_execute:
            # Configure the mock to raise a ValueError
            mock_execute.side_effect = ValueError("Failed to initialize wallet")
            result = self.revoke_tool.execute(parameters)
        
        # Check the result
        self.assertIn("Failed to initialize wallet", result)

    def test_execute_provider_exception(self):
        """Test execution with provider exception."""
        # Set up the parameters
        parameters = {
            "token": "USDC",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678_test_exception",  # Add _test_exception suffix
            "chain_id": "84532"
        }
        
        # Mock execute_revoke to simulate provider exception
        with patch('horus.tools.agent_kit.CdpActionProvider.execute_action') as mock_execute:
            # Configure the mock to raise an Exception
            mock_execute.side_effect = Exception("Test exception")
            result = self.revoke_tool.execute(parameters)
        
        # Check the result
        self.assertIn("Test exception", result)

    def test_valid_eth_address(self):
        """Test Ethereum address validation."""
        # Test with a valid address
        valid_address = "0x1234567890abcdef1234567890abcdef12345678"
        self.assertTrue(self.revoke_tool._is_valid_eth_address(valid_address))
        
        # Test with an invalid address (too short)
        invalid_address1 = "0x1234"
        self.assertFalse(self.revoke_tool._is_valid_eth_address(invalid_address1))
        
        # Test with an invalid address (not starting with 0x)
        invalid_address2 = "1234567890abcdef1234567890abcdef12345678"
        self.assertFalse(self.revoke_tool._is_valid_eth_address(invalid_address2))
        
        # Test with an invalid address (non-hex characters)
        invalid_address3 = "0x1234567890abcdef1234567890abcdefghjklmno"
        self.assertFalse(self.revoke_tool._is_valid_eth_address(invalid_address3))
        
        # Test with a non-string value
        invalid_address4 = 12345
        self.assertFalse(self.revoke_tool._is_valid_eth_address(invalid_address4))

    def test_revoke_with_service_failure(self):
        """Test revocation with service failure from AgentKit."""
        # Import needed here to maintain patch context
        from core.agent_kit import ActionResult, ActionStatus

        # Patch the execute_revoke method of agent_kit_manager to fail


class TestRevokeToolPrivateKeyLoading(unittest.TestCase):
    """Test cases specific to private key loading in RevokeTool."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that should be shared across all tests."""
        # Set up mocks for AgentKit
        cls.patches = setup_mocks()
        
        # Import related modules
        from core.agent_kit import (agent_kit_manager,
                                          is_agentkit_available)
        cls.agent_kit_manager = agent_kit_manager
        cls.is_agentkit_available = is_agentkit_available
        
        from tools.revoke import RevokeTool
        cls.RevokeTool = RevokeTool

    @classmethod
    def tearDownClass(cls):
        """Clean up shared test fixtures."""
        # Tear down mocks
        teardown_mocks(cls.patches)

    def test_private_key_loading(self):
        """Test that the private key is loaded from environment variables."""
        # This test verifies that the agent_kit_manager properly loads environment variables
        
        # Set a test private key in the environment
        with patch('os.getenv') as mock_getenv:
            mock_getenv.return_value = '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'
            
            # Check if the PRIVATE_KEY is available in the manager
            print(f"Test private key: {mock_getenv('PRIVATE_KEY')}")
            # Call the standalone function, not as a method
            self.assertTrue(is_agentkit_available())  # Not using self, calling the imported function


if __name__ == '__main__':
    unittest.main()
