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
                    "swapRouter": "0xbe330043dbf77f92be10e3e3499d8da189d638cb",
                    "address": "0x1234567890abcdef1234567890abcdef12345678"
                },
                "1": {
                    "swapRouter": "0xe592427a0aece92de3edee1f18e0157c05861564",
                    "address": "0x3d9819210a31b4961b30ef54bE2aDc79A1313607"
                }
            }
        },
        {
            "name": "SushiSwap",
            "chains": {
                "84532": {
                    "router": "0x1b02da8cb0d097eb8d57a175b88c7d8b47997506",
                    "address": "0x5678901234abcdef5678901234abcdef56789012"
                }
            }
        },
        {
            "name": "Compound",
            "chains": {
                "1": {
                    "address": "0x3d9819210a31b4961b30ef54bE2aDc79A1313607"
                },
                "84532": {
                    "address": "0x1234567890abcdef1234567890abcdef12345678"
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


class TestRevokeTool(unittest.TestCase):
    """Test suite for the RevokeTool class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create patches for the imports
        self.mock_modules = {
            'coinbase_agentkit.action_providers.cdp.cdp_action_provider': MagicMock(),
            'coinbase_agentkit.action_providers.cdp.cdp_wallet_provider': MagicMock(),
            'coinbase_agentkit.types': MagicMock(),
        }
        
        # Set up ActionStatus
        self.mock_action_status = MagicMock()
        self.mock_action_status.SUCCESS = "SUCCESS"
        self.mock_action_status.ERROR = "ERROR"
        self.mock_modules['coinbase_agentkit.types'].ActionStatus = self.mock_action_status
        
        # Save original modules
        self.original_modules = dict(sys.modules)
        
        # Add mock modules to sys.modules
        for module_name, mock_module in self.mock_modules.items():
            sys.modules[module_name] = mock_module
            
        # Import RevokeTool
        from horus.tools.revoke import RevokeTool

        # Create mocks for wallet and action providers
        self.mock_wallet_provider = MagicMock()
        self.mock_action_provider = MagicMock()
        
        # Create a RevokeTool instance
        self.revoke_tool = RevokeTool(SAMPLE_TOKENS_CONFIG, SAMPLE_PROTOCOLS_CONFIG)
        
        # Mock the initialize_providers method
        self.revoke_tool.initialize_providers = MagicMock(
            return_value=(self.mock_wallet_provider, self.mock_action_provider)
        )
        
        # Mock the wallet
        self.mock_wallet = MagicMock()
        self.mock_wallet_provider.get_wallet.return_value = self.mock_wallet
        
        # Mock the is_valid_eth_address method to always return True
        self.revoke_tool._is_valid_eth_address = MagicMock(return_value=True)
        
        # Log setup
        logger.info("RevokeTool test setup complete")

    def tearDown(self):
        """Clean up after each test method."""
        # Restore original modules
        sys.modules.clear()
        sys.modules.update(self.original_modules)
        
    def test_initialization(self):
        """Test initialization of RevokeTool."""
        # Check that the tokens and protocols configs are stored correctly
        self.assertEqual(self.revoke_tool.tokens_config, SAMPLE_TOKENS_CONFIG)
        self.assertEqual(self.revoke_tool.protocols_config, SAMPLE_PROTOCOLS_CONFIG)
        
        # Check that the default chain ID is set correctly
        self.assertEqual(self.revoke_tool.get_default_chain_id(), "84532")
        
        # Check that the block explorers are set up
        self.assertIn("1", self.revoke_tool.block_explorers)
        self.assertIn("84532", self.revoke_tool.block_explorers)
        
    def test_get_token_address(self):
        """Test retrieving token addresses."""
        # Test getting a token address for a known token/chain
        address = self.revoke_tool.get_token_address("USDC", "84532")
        self.assertEqual(address, "0xf175520c52418dfe19c8098071a252da48cd1c19")
        
        # Test getting a token address for a non-existent token
        address = self.revoke_tool.get_token_address("NONEXISTENT", "84532")
        self.assertEqual(address, "unknown")
        
        # Test getting a token address for a known token but non-existent chain
        address = self.revoke_tool.get_token_address("USDC", "999")
        self.assertEqual(address, "unknown")
        
        # Test with integer chain_id (should be converted to string internally)
        address = self.revoke_tool.get_token_address("USDC", 1)
        self.assertEqual(address, "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")

    def test_get_protocol_info(self):
        """Test protocol info retrieval."""
        # Test valid protocol and chain combinations
        protocol_info = self.revoke_tool.get_protocol_info("Compound", "1")
        self.assertEqual(protocol_info, {"address": "0x3d9819210a31b4961b30ef54bE2aDc79A1313607"})
        
        protocol_info = self.revoke_tool.get_protocol_info("UniswapV3", "84532")
        self.assertEqual(protocol_info, {
            "swapRouter": "0xbe330043dbf77f92be10e3e3499d8da189d638cb",
            "address": "0x1234567890abcdef1234567890abcdef12345678"
        })
        
        # Test with integer chain_id
        protocol_info = self.revoke_tool.get_protocol_info("Compound", 84532)
        self.assertEqual(protocol_info, {"address": "0x1234567890abcdef1234567890abcdef12345678"})
        
        # Test protocol not found
        protocol_info = self.revoke_tool.get_protocol_info("NONEXISTENT", "1")
        self.assertIsNone(protocol_info)
        
        # Test chain not found for protocol
        protocol_info = self.revoke_tool.get_protocol_info("Compound", "999")
        self.assertIsNone(protocol_info)

    def test_get_explorer_url(self):
        """Test block explorer URL generation."""
        # Test supported chains
        explorer_url = self.revoke_tool.get_explorer_url("1", "0xabcdef1234567890")
        self.assertEqual(explorer_url, "https://etherscan.io/tx/0xabcdef1234567890")
        
        explorer_url = self.revoke_tool.get_explorer_url("84532", "0x123456")
        self.assertEqual(explorer_url, "https://sepolia.basescan.org/tx/0x123456")
        
        # Test unsupported chain
        explorer_url = self.revoke_tool.get_explorer_url("999", "0xabcdef")
        self.assertIsNone(explorer_url)

    def test_create_revoke_action(self):
        """Test revoke action creation."""
        # Create a revoke action
        action = self.revoke_tool.create_revoke_action(
            token_address="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
            spender_address="0x1234567890abcdef1234567890abcdef12345678",
            chain_id="1"
        )
        
        # Check that the action is correctly formatted
        expected_action = {
            "type": "revokeAllowance",
            "params": {
                "tokenAddress": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
                "spenderAddress": "0x1234567890abcdef1234567890abcdef12345678",
                "chainId": "1"
            }
        }
        self.assertEqual(action, expected_action)

    def test_execute_success_with_token_symbol(self):
        """Test execution with a token symbol."""
        # Configure mock action provider to return a successful result
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.result = {"transactionHash": "0xabcdef1234567890"}
        self.mock_action_provider.execute_action.return_value = mock_result
        
        # Mock get_explorer_url to return a URL
        self.revoke_tool.get_explorer_url = MagicMock(
            return_value="https://sepolia.basescan.org/tx/0xabcdef1234567890"
        )
        
        # Execute with token symbol
        parameters = {
            "token": "USDC",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_id": "84532"
        }
        result = self.revoke_tool.execute(parameters)
        
        # Check the result contains expected success messages
        self.assertIn("Successfully revoked approval", result)
        self.assertIn("Transaction: https://sepolia.basescan.org/tx/0xabcdef1234567890", result)
        
        # Verify the action provider was called with the correct parameters
        self.mock_action_provider.execute_action.assert_called_once()
        
        # Reset mocks for next test
        self.mock_action_provider.execute_action.reset_mock()

    def test_execute_success_with_token_address(self):
        """Test execution with a token address."""
        # Configure mock action provider to return a successful result
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.result = {"transactionHash": "0xabcdef1234567890"}
        self.mock_action_provider.execute_action.return_value = mock_result
        
        # Mock get_explorer_url to return a URL
        self.revoke_tool.get_explorer_url = MagicMock(
            return_value="https://sepolia.basescan.org/tx/0xabcdef1234567890"
        )
        
        # Execute with token address
        parameters = {
            "token_address": "0xf175520c52418dfe19c8098071a252da48cd1c19",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_id": "84532"
        }
        result = self.revoke_tool.execute(parameters)
        
        # Check the result contains expected success messages
        self.assertIn("Successfully revoked approval", result)
        self.assertIn("Transaction: https://sepolia.basescan.org/tx/0xabcdef1234567890", result)
        
        # Verify the action provider was called with the correct parameters
        self.mock_action_provider.execute_action.assert_called_once()

    def test_execute_success_with_protocol(self):
        """Test execution with a protocol name."""
        # Configure mock action provider to return a successful result
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.result = {"transactionHash": "0xabcdef1234567890"}
        self.mock_action_provider.execute_action.return_value = mock_result
        
        # Mock get_explorer_url to return a URL
        self.revoke_tool.get_explorer_url = MagicMock(
            return_value="https://sepolia.basescan.org/tx/0xabcdef1234567890"
        )
        
        # Execute with token symbol and protocol
        parameters = {
            "token": "USDC",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "protocol": "UniswapV3",
            "chain_id": "84532"
        }
        result = self.revoke_tool.execute(parameters)
        
        # Check the result contains expected success messages
        self.assertIn("Successfully revoked approval", result)
        self.assertIn("UniswapV3 protocol", result)
        self.assertIn("Transaction: https://sepolia.basescan.org/tx/0xabcdef1234567890", result)
        
        # Verify the action provider was called with the correct parameters
        self.mock_action_provider.execute_action.assert_called_once()

    def test_execute_missing_token(self):
        """Test execution with missing token information."""
        # Execute without token or token_address
        parameters = {
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_id": "84532"
        }
        result = self.revoke_tool.execute(parameters)
        
        # Check the result contains expected error message
        self.assertIn("Error: Token address is required for revocation", result)
        
        # Verify the action provider was not called
        self.mock_action_provider.execute_action.assert_not_called()

    def test_execute_missing_spender(self):
        """Test execution with missing spender address."""
        # Execute without spender_address
        parameters = {
            "token": "USDC",
            "chain_id": "84532"
        }
        result = self.revoke_tool.execute(parameters)
        
        # Check the result contains expected error message
        self.assertIn("Error: Spender address is required for revocation", result)
        
        # Verify the action provider was not called
        self.mock_action_provider.execute_action.assert_not_called()

    def test_execute_invalid_addresses(self):
        """Test execution with invalid addresses."""
        # Mock _is_valid_eth_address to return False for specific addresses
        def mock_validate_address(address):
            return address != "0xinvalid"
        
        self.revoke_tool._is_valid_eth_address.side_effect = mock_validate_address
        
        # Execute with invalid token address
        parameters1 = {
            "token_address": "0xinvalid",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_id": "84532"
        }
        result1 = self.revoke_tool.execute(parameters1)
        
        # Check the result contains expected error message
        self.assertIn("Error: Invalid token address format", result1)
        
        # Execute with invalid spender address
        parameters2 = {
            "token_address": "0xf175520c52418dfe19c8098071a252da48cd1c19",
            "spender_address": "0xinvalid",
            "chain_id": "84532"
        }
        result2 = self.revoke_tool.execute(parameters2)
        
        # Check the result contains expected error message
        self.assertIn("Error: Invalid spender address format", result2)
        
        # Verify the action provider was not called
        self.mock_action_provider.execute_action.assert_not_called()
        
        # Reset side_effect
        self.revoke_tool._is_valid_eth_address.side_effect = None
        self.revoke_tool._is_valid_eth_address.return_value = True

    def test_execute_invalid_chain_id(self):
        """Test execution with invalid chain ID."""
        # Execute with non-numeric chain ID
        parameters = {
            "token_address": "0xf175520c52418dfe19c8098071a252da48cd1c19",  # Use token_address instead of token symbol
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_id": "invalid"
        }
        result = self.revoke_tool.execute(parameters)
        
        # Check the result contains expected error message
        self.assertIn("Error: Invalid chain ID", result)
        
        # Verify the action provider was not called
        self.mock_action_provider.execute_action.assert_not_called()

    def test_execute_unknown_protocol(self):
        """Test execution with unknown protocol."""
        # Execute with non-existent protocol
        parameters = {
            "token": "USDC",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "protocol": "NonexistentProtocol",
            "chain_id": "84532"
        }
        result = self.revoke_tool.execute(parameters)
        
        # Check the result contains expected error message
        self.assertIn("Error: Unknown protocol", result)
        
        # Verify the action provider was not called
        self.mock_action_provider.execute_action.assert_not_called()

    def test_execute_api_error(self):
        """Test execution with API error."""
        # Configure mock action provider to return an error result
        mock_result = MagicMock()
        mock_result.status = "ERROR"
        mock_result.error = "API Error: Rate limit exceeded"
        self.mock_action_provider.execute_action.return_value = mock_result
        
        # Execute with valid parameters
        parameters = {
            "token": "USDC",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_id": "84532"
        }
        result = self.revoke_tool.execute(parameters)
        
        # Check the result contains expected error message
        self.assertIn("Failed to revoke approval: API Error: Rate limit exceeded", result)
        
        # Verify the action provider was called
        self.mock_action_provider.execute_action.assert_called_once()

    def test_execute_wallet_failure(self):
        """Test execution with wallet initialization failure."""
        # Configure mock wallet provider to return None
        self.mock_wallet_provider.get_wallet.return_value = None
        
        # Execute with valid parameters
        parameters = {
            "token": "USDC",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_id": "84532"
        }
        result = self.revoke_tool.execute(parameters)
        
        # Check the result contains expected error message
        self.assertIn("Error: Failed to initialize wallet", result)
        
        # Verify the action provider was not called
        self.mock_action_provider.execute_action.assert_not_called()
        
        # Reset mock for next test
        self.mock_wallet_provider.get_wallet.return_value = self.mock_wallet

    def test_execute_provider_exception(self):
        """Test execution with provider exception."""
        # Configure mock action provider to raise an exception
        self.mock_action_provider.execute_action.side_effect = Exception("Test exception")
        
        # Execute with valid parameters
        parameters = {
            "token": "USDC",
            "spender_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_id": "84532"
        }
        result = self.revoke_tool.execute(parameters)
        
        # Check the result contains expected error message
        self.assertIn("Error executing revocation: Test exception", result)
        
        # Verify the action provider was called
        self.mock_action_provider.execute_action.assert_called_once()
        
        # Reset side_effect for next test
        self.mock_action_provider.execute_action.side_effect = None

    def test_is_valid_eth_address(self):
        """Test Ethereum address validation."""
        # Restore original method
        self.revoke_tool._is_valid_eth_address = self.revoke_tool.__class__._is_valid_eth_address.__get__(self.revoke_tool, self.revoke_tool.__class__)
        
        # Test valid addresses
        self.assertTrue(self.revoke_tool._is_valid_eth_address("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"))
        self.assertTrue(self.revoke_tool._is_valid_eth_address("0xF175520C52418DFE19C8098071A252DA48CD1C19"))
        
        # Test invalid addresses
        self.assertFalse(self.revoke_tool._is_valid_eth_address("0x123"))  # Too short
        self.assertFalse(self.revoke_tool._is_valid_eth_address("0x123456789012345678901234567890123456789Z"))  # Invalid character
        self.assertFalse(self.revoke_tool._is_valid_eth_address("1234567890abcdef1234567890abcdef12345678"))  # Missing 0x prefix
        self.assertFalse(self.revoke_tool._is_valid_eth_address(123))  # Not a string


if __name__ == "__main__":
    unittest.main()
