#!/usr/bin/env python3
"""
Test script for the Withdrawal Tool.
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
        }
    ]
}

SAMPLE_USER_BALANCES = {
    "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266": {
        "84532": {
            "positions": [
                {
                    "protocol": "Beefy",
                    "symbol": "USDC-USDT-LP",
                    "tokenId": "123",
                    "contractKey": "beefyUSDC-USDT-Vault"
                },
                {
                    "protocol": "UniswapV3",
                    "symbol": "USDC-WETH-LP",
                    "tokenId": "456",
                    "liquidity": "1000000"
                }
            ]
        }
    }
}

SAMPLE_PROTOCOLS = {
    "protocols": [
        {
            "name": "Beefy",
            "chains": {
                "84532": {
                    "beefyUSDC-USDT-Vault": "0xDb9ADe9917F2b9F67F569112DeADe3506f2177b2"
                }
            },
            "abis": {
                "BeefyVault": [
                    {
                        "inputs": [
                            {
                                "internalType": "uint256",
                                "name": "tokenId",
                                "type": "uint256"
                            }
                        ],
                        "name": "withdraw",
                        "outputs": [],
                        "stateMutability": "nonpayable",
                        "type": "function"
                    }
                ]
            }
        },
        {
            "name": "UniswapV3",
            "chains": {
                "84532": {
                    "nonfungiblePositionManager": "0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2"
                }
            },
            "abis": {
                "NonfungiblePositionManager": [
                    {
                        "inputs": [
                            {
                                "internalType": "uint256",
                                "name": "tokenId",
                                "type": "uint256"
                            },
                            {
                                "internalType": "uint128",
                                "name": "liquidity",
                                "type": "uint128"
                            },
                            {
                                "internalType": "uint256",
                                "name": "amount0Min",
                                "type": "uint256"
                            },
                            {
                                "internalType": "uint256",
                                "name": "amount1Min",
                                "type": "uint256"
                            },
                            {
                                "internalType": "uint256",
                                "name": "deadline",
                                "type": "uint256"
                            }
                        ],
                        "name": "decreaseLiquidity",
                        "outputs": [],
                        "stateMutability": "nonpayable",
                        "type": "function"
                    },
                    {
                        "inputs": [
                            {
                                "internalType": "uint256",
                                "name": "tokenId",
                                "type": "uint256"
                            },
                            {
                                "internalType": "address",
                                "name": "recipient",
                                "type": "address"
                            },
                            {
                                "internalType": "uint128",
                                "name": "amount0Max",
                                "type": "uint128"
                            },
                            {
                                "internalType": "uint128",
                                "name": "amount1Max",
                                "type": "uint128"
                            }
                        ],
                        "name": "collect",
                        "outputs": [],
                        "stateMutability": "nonpayable",
                        "type": "function"
                    }
                ]
            }
        }
    ]
}


class TestWithdrawalTool(unittest.TestCase):
    """Test case for the WithdrawalTool."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a mock for CdpActionProvider
        self.mock_action_provider = MagicMock()
        self.mock_wallet_provider = MagicMock()
        
        # Configure the mock to return a success result
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.transaction_hash = "0x1234567890abcdef"
        mock_result.message = "Transaction successful"
        self.mock_action_provider.execute_contract_write.return_value = mock_result
        
        # Configure wallet provider to return a default account
        self.mock_wallet_provider.get_default_account.return_value = "0xDefaultAccount"
        
        # Create patches
        self.action_provider_patcher = patch('horus.tools.withdrawal.CdpActionProvider')
        self.wallet_provider_patcher = patch('horus.tools.withdrawal.CdpWalletProvider')
        
        # Start the patches
        mock_action_provider_class = self.action_provider_patcher.start()
        mock_wallet_provider_class = self.wallet_provider_patcher.start()
        
        # Configure the mock classes to return our mocks
        mock_action_provider_class.return_value = self.mock_action_provider
        mock_wallet_provider_class.return_value = self.mock_wallet_provider
        
        # Mark AgentKit as available
        with patch('horus.tools.withdrawal.AGENTKIT_AVAILABLE', True):
            self.withdrawal_tool = WithdrawalTool(
                SAMPLE_DEPENDENCY_GRAPH,
                SAMPLE_USER_BALANCES,
                SAMPLE_PROTOCOLS
            )
        
        # Set the mocks directly on the instance
        self.withdrawal_tool._cdp_action_provider = self.mock_action_provider
        self.withdrawal_tool._cdp_wallet_provider = self.mock_wallet_provider
    
    def tearDown(self):
        """Clean up after the test."""
        # Stop the patches
        self.action_provider_patcher.stop()
        self.wallet_provider_patcher.stop()
    
    def test_get_user_positions(self):
        """Test retrieving user positions."""
        positions = self.withdrawal_tool.get_user_positions(
            "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266",
            "84532"
        )
        
        self.assertEqual(len(positions), 2)
        self.assertEqual(positions[0]["protocol"], "Beefy")
        self.assertEqual(positions[1]["protocol"], "UniswapV3")
    
    def test_get_exit_functions(self):
        """Test retrieving exit functions for a token."""
        exit_functions = self.withdrawal_tool.get_exit_functions_for_token("USDC-USDT-LP", "84532")
        
        self.assertEqual(len(exit_functions), 1)
        self.assertEqual(exit_functions[0]["contractType"], "BeefyVault")
        self.assertEqual(exit_functions[0]["functionName"], "withdraw")
    
    def test_get_protocol_contract(self):
        """Test retrieving protocol contract addresses."""
        address = self.withdrawal_tool.get_protocol_contract("Beefy", "beefyUSDC-USDT-Vault", "84532")
        self.assertEqual(address, "0xDb9ADe9917F2b9F67F569112DeADe3506f2177b2")
        
        address = self.withdrawal_tool.get_protocol_contract("UniswapV3", "nonfungiblePositionManager", "84532")
        self.assertEqual(address, "0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2")
    
    def test_execute_beefy_withdrawal(self):
        """Test executing a withdrawal from Beefy."""
        position = {
            "protocol": "Beefy",
            "symbol": "USDC-USDT-LP",
            "tokenId": "123",
            "contractKey": "beefyUSDC-USDT-Vault"
        }
        
        result = self.withdrawal_tool.execute_beefy_withdrawal(position, "84532")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["transaction_hash"], "0x1234567890abcdef")
        
        # Check that the action provider was called with correct parameters
        self.mock_action_provider.execute_contract_write.assert_called_once_with(
            chain_id="84532",
            account="0xDefaultAccount",
            contract_address="0xDb9ADe9917F2b9F67F569112DeADe3506f2177b2",
            function_name="withdraw",
            args=["123"]
        )
    
    def test_execute_uniswap_withdrawal(self):
        """Test executing a withdrawal from UniswapV3."""
        position = {
            "protocol": "UniswapV3",
            "symbol": "USDC-WETH-LP",
            "tokenId": "456",
            "liquidity": "1000000"
        }
        
        # Mock the decrease liquidity and collect calls
        decrease_result = MagicMock()
        decrease_result.status = "SUCCESS"
        decrease_result.transaction_hash = "0xdecrease"
        decrease_result.message = "Liquidity decreased"
        
        collect_result = MagicMock()
        collect_result.status = "SUCCESS"
        collect_result.transaction_hash = "0xcollect"
        collect_result.message = "Tokens collected"
        
        self.mock_action_provider.execute_contract_write.side_effect = [
            decrease_result,
            collect_result
        ]
        
        result = self.withdrawal_tool.execute_uniswap_withdrawal(position, "84532")
        
        self.assertTrue(result["success"])
        self.assertEqual(result["transaction_hash"], "0xcollect")
        
        # Check that the action provider was called with correct parameters for both steps
        self.assertEqual(self.mock_action_provider.execute_contract_write.call_count, 2)
        
        # Check first call (decreaseLiquidity)
        args, kwargs = self.mock_action_provider.execute_contract_write.call_args_list[0]
        self.assertEqual(kwargs["chain_id"], "84532")
        self.assertEqual(kwargs["contract_address"], "0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2")
        self.assertEqual(kwargs["function_name"], "decreaseLiquidity")
        self.assertEqual(kwargs["args"][0], "456")  # tokenId
        self.assertEqual(kwargs["args"][1], "1000000")  # liquidity
        
        # Check second call (collect)
        args, kwargs = self.mock_action_provider.execute_contract_write.call_args_list[1]
        self.assertEqual(kwargs["chain_id"], "84532")
        self.assertEqual(kwargs["contract_address"], "0x27F971cb582BF9E50F397e4d29a5C7A34f11faA2")
        self.assertEqual(kwargs["function_name"], "collect")
        self.assertEqual(kwargs["args"][0], "456")  # tokenId
    
    def test_execute_withdrawal(self):
        """Test the main execute method with multiple positions."""
        # Reset the mock to return success for all calls
        self.mock_action_provider.execute_contract_write.side_effect = None
        mock_result = MagicMock()
        mock_result.status = "SUCCESS"
        mock_result.transaction_hash = "0xabcdef1234567890"
        mock_result.message = "Success"
        self.mock_action_provider.execute_contract_write.return_value = mock_result
        
        # Define parameters
        parameters = {
            "token": "USDC-USDT-LP",
            "amount": "ALL",
            "destination": "safe_wallet",
            "chain_id": "84532",
            "user_address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
        }
        
        # Execute the withdrawal
        result = self.withdrawal_tool.execute(parameters)
        
        # Check that the result contains the expected information
        self.assertIn("Emergency withdrawal initiated", result)
        self.assertIn("Results: 1 successful", result)
        self.assertIn("Success", result)
        self.assertIn("0xabcdef1234567890", result)
    
    def test_no_matching_positions(self):
        """Test executing a withdrawal with no matching positions."""
        parameters = {
            "token": "NON_EXISTENT_TOKEN",
            "amount": "ALL",
            "destination": "safe_wallet",
            "chain_id": "84532",
            "user_address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
        }
        
        # Execute the withdrawal
        result = self.withdrawal_tool.execute(parameters)
        
        # Check that the result contains the expected error message
        self.assertIn("no matching positions found", result)
        self.assertEqual(self.mock_action_provider.execute_contract_write.call_count, 0)
    
    def test_callable_interface(self):
        """Test the callable interface of WithdrawalTool."""
        # Mock the execute method
        self.withdrawal_tool.execute = MagicMock(return_value="Executed successfully")
        
        # Call the instance directly
        parameters = {"token": "test"}
        result = self.withdrawal_tool(parameters)
        
        # Check that execute was called with the parameters
        self.withdrawal_tool.execute.assert_called_once_with(parameters)
        self.assertEqual(result, "Executed successfully")
        
    def test_simulation_mode(self):
        """Test the tool in simulation mode when AgentKit is not available."""
        # Create a new instance with AGENTKIT_AVAILABLE set to False
        with patch('horus.tools.withdrawal.AGENTKIT_AVAILABLE', False):
            withdrawal_tool = WithdrawalTool(
                SAMPLE_DEPENDENCY_GRAPH,
                SAMPLE_USER_BALANCES,
                SAMPLE_PROTOCOLS
            )
            
            # Execute a withdrawal that should be simulated
            position = {
                "protocol": "Beefy",
                "symbol": "USDC-USDT-LP",
                "tokenId": "123",
                "contractKey": "beefyUSDC-USDT-Vault"
            }
            
            result = withdrawal_tool.execute_beefy_withdrawal(position, "84532")
            
            # Check that we got a simulated response
            self.assertTrue(result["success"])
            self.assertEqual(result["transaction_hash"], "0xabcdef1234567890")
            self.assertIn("Simulated withdrawal", result["message"])


if __name__ == "__main__":
    unittest.main() 