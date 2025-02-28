#!/usr/bin/env python3
"""
Test script for the Security Agent.
"""
import json
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock, mock_open, patch

from dotenv import load_dotenv

# Mock coinbase_agentkit dependencies before imports
# Create mock classes for the imports that will fail
mock_action_status = MagicMock()
mock_action_status.SUCCESS = "SUCCESS"

# Create system for patching imports
mock_modules = {
    'coinbase_agentkit.action_providers.cdp.cdp_action_provider': MagicMock(),
    'coinbase_agentkit.action_providers.cdp.cdp_wallet_provider': MagicMock(),
    'coinbase_agentkit.types': MagicMock(),
}

# Set up ActionStatus
mock_modules['coinbase_agentkit.types'].ActionStatus = mock_action_status
mock_modules['coinbase_agentkit.types'].ActionResult = MagicMock

# Patch sys.modules to include our mocks
for module_name, mock_module in mock_modules.items():
    sys.modules[module_name] = mock_module

# Now we can import OpenAI
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the security agent
from horus.agents.security_agent import SecurityAgent

# Mock the coinbase_agentkit modules before importing any tools
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

# Now import the security agent
from horus.agents.security_agent import SecurityAgent

# Sample test data for mocking
SAMPLE_DEPENDENCY_GRAPH = {
    "nodes": [
        {
            "symbol": "USDC-USDT-LP",
            "chainId": "84532",
            "exitFunctions": [
                {
                    "contractType": "BeefyVault",
                    "functionName": "withdraw",
                    "contractAddress": "0xDb9ADe9917F2b9F67F569112DeADe3506f2177b2"
                }
            ]
        },
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

SAMPLE_USER_BALANCES = {
    "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266": {
        "84532": {
            "USDC": "1000.0",
            "ETH": "5.0",
            "positions": [
                {
                    "protocol": "Beefy",
                    "symbol": "USDC-USDT-LP",
                    "tokenId": "123",
                    "contractKey": "beefyUSDC-USDT-Vault"
                }
            ]
        }
    }
}

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
            "name": "Beefy",
            "chains": {
                "84532": {
                    "beefyUSDC-USDT-Vault": "0xDb9ADe9917F2b9F67F569112DeADe3506f2177b2"
                }
            }
        },
        {
            "name": "UniswapV3",
            "chains": {
                "84532": {
                    "swapRouter": "0xbe330043dbf77f92be10e3e3499d8da189d638cb"
                }
            }
        }
    ]
}


class TestSecurity(unittest.TestCase):
    """Test case for the Security Agent functionality."""
    
    def setUp(self):
        """Set up the test."""
        # Mock open to avoid file system access
        self.open_patcher = patch('builtins.open', mock_open(read_data='{}'))
        self.mock_open = self.open_patcher.start()
        
        # Mock os.path.exists to always return True
        self.exists_patcher = patch('os.path.exists', return_value=True)
        self.exists_patcher.start()
        
        # Mock os.path.dirname to avoid file system access
        self.dirname_patcher = patch('os.path.dirname', return_value='/mock/path')
        self.dirname_patcher.start()
        
        # Mock os.path.join to avoid file system access
        self.join_patcher = patch('os.path.join', side_effect=lambda *args: '/'.join(args))
        self.join_patcher.start()
        
        # Create a mock OpenAI client
        self.mock_openai_client = MagicMock()
        self.mock_openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content="Mock response"))
        ]
        
        # Create the security agent with mocked dependencies
        self.security_agent = SecurityAgent(self.mock_openai_client)
        
        # Mock the tools directly
        self.security_agent.withdrawal_tool = MagicMock(return_value="Funds withdrawn successfully")
        self.security_agent.revoke_tool = MagicMock(return_value="Permissions revoked successfully")
        self.security_agent.swap_tool = MagicMock(return_value="Tokens swapped successfully")
        self.security_agent.monitor_tool = MagicMock(return_value="Monitoring set up successfully")
    
    def tearDown(self):
        """Clean up after the test."""
        self.open_patcher.stop()
        self.exists_patcher.stop()
        self.dirname_patcher.stop()
        self.join_patcher.stop()
        
        # Reset mocks between tests to avoid unexpected call counts
        if hasattr(self, 'security_agent'):
            self.security_agent.withdrawal_tool.reset_mock()
            self.security_agent.revoke_tool.reset_mock()
            self.security_agent.swap_tool.reset_mock()
            self.security_agent.monitor_tool.reset_mock()
    
    def test_security_alert(self):
        """Test processing a security alert."""
        # Arrange
        alert = "SECURITY ALERT: Critical vulnerability in the Beefy protocol putting all funds at risk."
        
        # Set up the mock OpenAI client to return a withdrawal action
        self.mock_openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "action_plan": {
                    "action_type": "withdraw",
                    "parameters": {
                        "token": "USDC",
                        "amount": "all",
                        "destination_address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
                        "chain_id": "1"
                    }
                }
            })))
        ]
        
        # Act
        result = self.security_agent.process_alert(alert)
        
        # Assert
        self.assertEqual(result, "Funds withdrawn successfully")
        self.security_agent.withdrawal_tool.assert_called_once()
    
    def test_revoke_tool(self):
        """Test the revoke tool."""
        # Arrange
        alert = "SECURITY ALERT: Urgent warning - unusual approval activity detected for your tokens. Revoke permissions immediately!"
        
        # Set up the mock OpenAI client to return a revoke action
        self.mock_openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "action_plan": {
                    "action_type": "revoke",
                    "parameters": {
                        "token": "USDC",
                        "protocol": "UniswapV3",
                        "spender_address": "0xAdb1678064eB383B18795c701f1473f7d1795183",
                        "chain_id": "1"
                    }
                }
            })))
        ]
        
        # Act
        result = self.security_agent.process_alert(alert)
        
        # Assert
        self.assertEqual(result, "Permissions revoked successfully")
        self.security_agent.revoke_tool.assert_called_once()
    
    def test_swap_tool(self):
        """Test the swap tool."""
        # Arrange
        alert = "SECURITY ALERT: ETH price volatility detected. Consider swapping to stablecoins."
        
        # Mock the parse_ai_response method to return a swap action
        self.mock_openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "action_plan": {
                    "action_type": "swap",
                    "parameters": {
                        "token_in": "ETH",
                        "token_out": "USDC",
                        "amount_in": "1.5",
                        "chain_id": "1"
                    }
                }
            })))
        ]
        
        # Act
        result = self.security_agent.process_alert(alert)
        
        # Assert
        self.assertEqual(result, "Tokens swapped successfully")
        self.security_agent.swap_tool.assert_called_once()
    
    def test_monitor_tool(self):
        """Test the monitor tool."""
        # Arrange
        alert = "SECURITY ALERT: Recent fluctuations in DeFi protocols. Please set up monitoring for your positions."
        
        # Mock the parse_ai_response method to return a monitor action
        self.mock_openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "action_plan": {
                    "action_type": "monitor",
                    "parameters": {
                        "asset": "All Positions",
                        "duration": "24h",
                        "threshold": "5%"
                    }
                }
            })))
        ]
        
        # Act
        result = self.security_agent.process_alert(alert)
        
        # Assert
        self.assertEqual(result, "Monitoring set up successfully")
        self.security_agent.monitor_tool.assert_called_once()
    
    def test_parse_ai_response_json(self):
        """Test parsing a structured JSON response from the AI."""
        # Sample JSON response
        json_response = json.dumps({
            "action_plan": [
                {
                    "action": "swap",
                    "parameters": {
                        "token_in": "ETH",
                        "token_out": "USDC",
                        "amount_in": "1.0",
                        "chain_id": "84532"
                    }
                }
            ]
        })
        
        # Parse the response
        action_type, parameters = self.security_agent.parse_ai_response(json_response)
        
        # Check that the correct action and parameters were extracted
        self.assertEqual(action_type, "swap")
        self.assertEqual(parameters["token_in"], "ETH")
        self.assertEqual(parameters["token_out"], "USDC")
        self.assertEqual(parameters["amount_in"], "1.0")
        self.assertEqual(parameters["chain_id"], "84532")
    
    def test_parse_ai_response_text(self):
        """Test parsing a text response from the AI."""
        # Sample text response with action hints
        text_response = """
        Based on the security alert, I recommend swapping ETH to USDC immediately.
        
        Parameters:
        - token_in: ETH
        - token_out: USDC
        - amount_in: 1.0
        - chain_id: 84532
        """
        
        # Parse the response
        action_type, parameters = self.security_agent.parse_ai_response(text_response)
        
        # Check that the correct action and parameters were extracted
        self.assertEqual(action_type, "swap")
        self.assertEqual(parameters["token_in"], "ETH")
        self.assertEqual(parameters["token_out"], "USDC")
        self.assertEqual(parameters["amount_in"], "1.0")
        self.assertEqual(parameters["chain_id"], "84532")
    
    def test_integration(self):
        """Test the entire security agent flow with different alert types."""
        # Reset mocks
        self.security_agent.withdrawal_tool.reset_mock()
        self.security_agent.revoke_tool.reset_mock()
        self.security_agent.swap_tool.reset_mock()
        self.security_agent.monitor_tool.reset_mock()
        
        # Test case 1: Withdrawal
        alert1 = "SECURITY ALERT: Critical vulnerability in the Beefy protocol putting all funds at risk."
        
        # Set up the OpenAI client mock for withdrawal
        self.mock_openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "action_plan": {
                    "action_type": "withdraw",
                    "parameters": {
                        "token": "USDC",
                        "amount": "all",
                        "destination_address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
                        "chain_id": "1"
                    }
                }
            })))
        ]
        
        result1 = self.security_agent.process_alert(alert1)
        self.assertEqual(result1, "Funds withdrawn successfully")
        self.security_agent.withdrawal_tool.assert_called_once()
        
        # Test case 2: Revoke
        alert2 = "SECURITY ALERT: Suspicious approval activity detected. Revoke permissions immediately."
        
        # Set up the OpenAI client mock for revoke
        self.mock_openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "action_plan": {
                    "action_type": "revoke",
                    "parameters": {
                        "token": "USDC",
                        "protocol": "UniswapV3",
                        "spender_address": "0xAdb1678064eB383B18795c701f1473f7d1795183",
                        "chain_id": "1"
                    }
                }
            })))
        ]
        
        result2 = self.security_agent.process_alert(alert2)
        self.assertEqual(result2, "Permissions revoked successfully")
        self.security_agent.revoke_tool.assert_called_once()
        
        # Test case 3: Swap
        alert3 = "SECURITY ALERT: ETH price drop anticipated. Swap to stablecoins recommended."
        
        # Set up the OpenAI client mock for swap
        self.mock_openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "action_plan": {
                    "action_type": "swap",
                    "parameters": {
                        "token_in": "ETH",
                        "token_out": "USDC",
                        "amount_in": "all",
                        "chain_id": "1"
                    }
                }
            })))
        ]
        
        result3 = self.security_agent.process_alert(alert3)
        self.assertEqual(result3, "Tokens swapped successfully")
        self.security_agent.swap_tool.assert_called_once()
        
        # Test case 4: Monitor
        alert4 = "SECURITY ALERT: Unusual activity in the market. Set up enhanced monitoring."
        
        # Set up the OpenAI client mock for monitor
        self.mock_openai_client.chat.completions.create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "action_plan": {
                    "action_type": "monitor",
                    "parameters": {
                        "asset": "All Positions",
                        "duration": "24h",
                        "threshold": "5%"
                    }
                }
            })))
        ]
        
        result4 = self.security_agent.process_alert(alert4)
        self.assertEqual(result4, "Monitoring set up successfully")
        self.security_agent.monitor_tool.assert_called_once()


if __name__ == "__main__":
    unittest.main()
