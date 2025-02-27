#!/usr/bin/env python3
"""
Unit tests for the WithdrawalTool class in the Horus security system.

This test suite provides comprehensive testing for the WithdrawalTool class,
covering its initialization, token address resolution, validation, and
execution of withdrawal operations.
"""
import json
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from dotenv import load_dotenv
# Import the mock_agent_kit utilities
from tests.mock_agent_kit import setup_mocks, teardown_mocks

# Configure logging for test
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import AGENTKIT_AVAILABLE from the withdrawal module
from horus.tools.withdrawal import AGENTKIT_AVAILABLE

# Mock the coinbase_agentkit modules before importing WithdrawalTool
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
    def __init__(self, status="SUCCESS", transaction_hash="0xtest", message="Test successful"):
        self.status = status
        self.transaction_hash = transaction_hash
        self.message = message

sys.modules['coinbase_agentkit.types'].ActionResult = MockActionResult

# Now import the withdrawal tool
from horus.tools.withdrawal import WithdrawalTool

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
        }
    ]
}

SAMPLE_PROTOCOLS_CONFIG = {
    "protocols": [
        {
            "name": "Coinbase",
            "chains": {
                "84532": {
                    "exchange_id": "coinbase_pro"
                },
                "1": {
                    "exchange_id": "coinbase_pro"
                }
            }
        }
    ]
}

class TestWithdrawalTool(unittest.TestCase):
    """Test cases for the WithdrawalTool class."""

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that should be shared across all tests."""
        # Set up mocks for AgentKit
        cls.patches = setup_mocks()
        
        # Import WithdrawalTool after setting up mocks
        from horus.tools.withdrawal import WithdrawalTool
        cls.WithdrawalTool = WithdrawalTool
        
        from horus.tools.agent_kit import agent_kit_manager
        cls.agent_kit_manager = agent_kit_manager

    @classmethod
    def tearDownClass(cls):
        """Clean up shared test fixtures."""
        # Tear down mocks
        teardown_mocks(cls.patches)

    def setUp(self):
        """Set up test fixtures before each test."""
        logger.info("WithdrawalTool test setup complete")
        self.withdrawal_tool = self.WithdrawalTool(SAMPLE_TOKENS_CONFIG, SAMPLE_PROTOCOLS_CONFIG)

    def test_init(self):
        """Test initialization of WithdrawalTool."""
        self.assertEqual(self.withdrawal_tool.name, "withdrawal")
        self.assertEqual(self.withdrawal_tool.tokens_config, SAMPLE_TOKENS_CONFIG)
        self.assertIsNotNone(self.withdrawal_tool.block_explorers)

    def test_get_token_address(self):
        """Test token address resolution."""
        # Test with a known token and chain
        token_address = self.withdrawal_tool.get_token_address("USDC", "84532")
        self.assertEqual(token_address, "0xf175520c52418dfe19c8098071a252da48cd1c19")
        
        # Test with a known token and different chain
        token_address = self.withdrawal_tool.get_token_address("USDC", "1")
        self.assertEqual(token_address, "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")
        
        # Test with an unknown token
        token_address = self.withdrawal_tool.get_token_address("NONEXISTENT", "84532")
        self.assertEqual(token_address, "unknown")
        
        # Test with an unknown chain
        token_address = self.withdrawal_tool.get_token_address("USDC", "999")
        self.assertEqual(token_address, "unknown")

    def test_get_explorer_url(self):
        """Test block explorer URL generation."""
        # Test with a known chain
        tx_hash = "0x1234567890abcdef1234567890abcdef12345678"
        explorer_url = self.withdrawal_tool.get_explorer_url("84532", tx_hash)
        expected_url = f"https://sepolia.basescan.org/tx/{tx_hash}"
        self.assertEqual(explorer_url, expected_url)
        
        # Test with an unknown chain
        explorer_url = self.withdrawal_tool.get_explorer_url("999", tx_hash)
        self.assertIsNone(explorer_url)

    def test_valid_eth_address(self):
        """Test Ethereum address validation."""
        # Test with a valid address
        valid_address = "0x1234567890abcdef1234567890abcdef12345678"
        self.assertTrue(self.withdrawal_tool._is_valid_eth_address(valid_address))
        
        # Test with an invalid address (too short)
        invalid_address1 = "0x1234"
        self.assertFalse(self.withdrawal_tool._is_valid_eth_address(invalid_address1))
        
        # Test with an invalid address (not starting with 0x)
        invalid_address2 = "1234567890abcdef1234567890abcdef12345678"
        self.assertFalse(self.withdrawal_tool._is_valid_eth_address(invalid_address2))
        
        # Test with an invalid address (non-hex characters)
        invalid_address3 = "0x1234567890abcdef1234567890abcdefghjklmno"
        self.assertFalse(self.withdrawal_tool._is_valid_eth_address(invalid_address3))
        
        # Test with a non-string value
        invalid_address4 = 12345
        self.assertFalse(self.withdrawal_tool._is_valid_eth_address(invalid_address4))

    def test_validate_parameters(self):
        """Test parameter validation."""
        # Test with valid parameters
        valid_params = {
            "token": "USDC",
            "destination_address": "0x1234567890abcdef1234567890abcdef12345678",
            "amount": "100",
            "chain_id": "84532"
        }
        result = self.withdrawal_tool.validate_parameters(valid_params)
        self.assertIsNone(result)
        
        # Test with missing token
        missing_token = {
            "destination_address": "0x1234567890abcdef1234567890abcdef12345678",
            "amount": "100",
            "chain_id": "84532"
        }
        result = self.withdrawal_tool.validate_parameters(missing_token)
        self.assertIn("Error: Missing token information", result)
        
        # Test with missing destination address
        missing_dest = {
            "token": "USDC",
            "amount": "100",
            "chain_id": "84532"
        }
        result = self.withdrawal_tool.validate_parameters(missing_dest)
        self.assertIn("Error: Missing destination address", result)
        
        # Test with missing amount
        missing_amount = {
            "token": "USDC",
            "destination_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_id": "84532"
        }
        result = self.withdrawal_tool.validate_parameters(missing_amount)
        self.assertIn("Error: Missing withdrawal amount", result)
        
        # Test with invalid destination address
        invalid_dest = {
            "token": "USDC",
            "destination_address": "0xinvalid",
            "amount": "100",
            "chain_id": "84532"
        }
        result = self.withdrawal_tool.validate_parameters(invalid_dest)
        self.assertIn("Error: Invalid destination address format", result)
        
        # Test with invalid chain ID
        invalid_chain = {
            "token": "USDC",
            "destination_address": "0x1234567890abcdef1234567890abcdef12345678",
            "amount": "100",
            "chain_id": "invalid"
        }
        result = self.withdrawal_tool.validate_parameters(invalid_chain)
        self.assertIn("Error: Invalid chain ID", result)
        
        # Test with unknown token
        unknown_token = {
            "token": "UNKNOWN",
            "destination_address": "0x1234567890abcdef1234567890abcdef12345678",
            "amount": "100",
            "chain_id": "84532"
        }
        result = self.withdrawal_tool.validate_parameters(unknown_token)
        self.assertIn("Error: Could not resolve address for token", result)
        
        # Test with invalid token address
        invalid_token_addr = {
            "token_address": "0xinvalid",
            "destination_address": "0x1234567890abcdef1234567890abcdef12345678",
            "amount": "100",
            "chain_id": "84532"
        }
        result = self.withdrawal_tool.validate_parameters(invalid_token_addr)
        self.assertIn("Error: Invalid token address format", result)

    def test_execute_success(self):
        """Test successful withdrawal execution."""
        # Set up test parameters
        params = {
            "token": "USDC",
            "destination_address": "0x1234567890abcdef1234567890abcdef12345678",
            "amount": "100",
            "chain_id": "84532",
            "exchange": "Coinbase"
        }
        
        # Test with a successful response
        with patch('horus.tools.agent_kit.agent_kit_manager.execute_withdrawal') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "transaction_hash": "0x123456789abcdef123456789abcdef123456789abcdef123456789abcdef",
                "message": "Withdrawal executed successfully"
            }
            result = self.withdrawal_tool.execute(params)
        
        # Check the result
        self.assertIn("Successfully withdrew", result)
        self.assertIn("100", result)
        self.assertIn("USDC", result)

    def test_execute_failure(self):
        """Test withdrawal execution failure."""
        # Set up test parameters
        params = {
            "token": "USDC",
            "destination_address": "0x1234567890abcdef1234567890abcdef12345678",
            "amount": "100",
            "chain_id": "84532",
            "exchange": "Coinbase"
        }
        
        # Test with a failure response
        with patch('horus.tools.agent_kit.agent_kit_manager.execute_withdrawal') as mock_execute:
            # Configure the mock to return a failure result
            mock_execute.return_value = {
                "success": False,
                "transaction_hash": None,
                "message": "API Error: Rate limit exceeded"
            }
            result = self.withdrawal_tool.execute(params)
        
        # Check the result
        self.assertIn("Failed to execute withdrawal", result)
        self.assertIn("API Error: Rate limit exceeded", result)

    def test_execute_exception(self):
        """Test withdrawal execution with exception."""
        # Set up test parameters
        params = {
            "token": "USDC",
            "destination_address": "0x1234567890abcdef1234567890abcdef12345678",
            "amount": "100",
            "chain_id": "84532",
            "exchange": "Coinbase"
        }
        
        # Test with an exception
        with patch('horus.tools.agent_kit.agent_kit_manager.execute_withdrawal') as mock_execute:
            # Configure the mock to raise an exception
            mock_execute.side_effect = Exception("Test exception")
            result = self.withdrawal_tool.execute(params)
        
        # Check the result
        self.assertIn("Error executing withdrawal", result)
        self.assertIn("Test exception", result)

    def test_simulation_mode(self):
        """Test simulation mode."""
        # Set up test parameters with simulation flag
        params = {
            "token": "USDC",
            "destination_address": "0x1234567890abcdef1234567890abcdef12345678",
            "amount": "100",
            "chain_id": "84532",
            "exchange": "Coinbase",
            "simulation": True
        }
        
        # Execute in simulation mode
        result = self.withdrawal_tool.execute(params)
        
        # Check the result
        self.assertIn("SIMULATION", result)
        self.assertIn("Would withdraw", result)
        self.assertIn("100", result)
        self.assertIn("USDC", result)


if __name__ == '__main__':
    unittest.main() 