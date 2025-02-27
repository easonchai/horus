#!/usr/bin/env python3
"""
Test script for the Security Agent.
"""
import json
import logging
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

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


# Define a class for the test case to help with mocking
class TestSecurity(unittest.TestCase):
    """Test case for the security agent."""
    
    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{}')
    @patch('json.load', return_value={})
    def test_security_alert(self, mock_json_load, mock_open, mock_path_exists):
        """
        Test the security agent's ability to process security alerts.
        """
        # Set up mock for json.load to return specific data for each file
        mock_path_exists.return_value = True
        mock_json_load.side_effect = [
            {"dependencies": []},  # dependency_graph
            {"users": []},         # user_balances
            {"tokens": []},        # tokens_config
            {"protocols": []}      # protocols_config
        ]
        
        # Mock OpenAI client
        mock_openai = MagicMock()
        
        # Create security agent with mock OpenAI
        security_agent = SecurityAgent(mock_openai, mock_openai=True)
        
        # Mock the tools
        security_agent.withdrawal_tool = MagicMock(return_value="Funds withdrawn successfully.")
        security_agent.revoke_tool = MagicMock(return_value="Permissions revoked successfully.")
        security_agent.monitor_tool = MagicMock(return_value="Monitoring set up successfully.")
        
        # Process a test alert
        test_alert = """
        CRITICAL SECURITY ALERT: Beefy protocol vulnerability detected on Base!
        
        A critical vulnerability has been identified in the Beefy protocol's vault contracts
        on the Base chain. This vulnerability could allow an attacker to drain funds from affected vaults.
        
        Affected users: All users with beefyUSDC-USDT positions on Base
        Risk level: HIGH
        Recommendation: Withdraw funds immediately
        """
        
        # Execute the test
        result = security_agent.process_security_alert(test_alert)
        
        # Print the result
        print("\nSecurity Alert Processing Result:")
        print("-" * 50)
        print(result)
        print("-" * 50)
        
        # Assert that withdrawal_tool was called due to "vulnerability" in the alert
        security_agent.withdrawal_tool.assert_called_once()
        self.assertIn("withdrawn successfully", result)

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{}')
    @patch('json.load', return_value={})
    def test_revoke_tool(self, mock_json_load, mock_open, mock_path_exists):
        """
        Test the revoke tool directly.
        """
        # Set up mock for json.load to return specific data for each file
        mock_path_exists.return_value = True
        mock_json_load.side_effect = [
            {"dependencies": []},  # dependency_graph
            {"users": []},         # user_balances
            {"tokens": []},        # tokens_config
            {"protocols": []}      # protocols_config
        ]
        
        # Mock OpenAI client
        mock_openai = MagicMock()
        
        # Create security agent
        security_agent = SecurityAgent(mock_openai)
        
        # Mock the revoke tool
        security_agent.revoke_tool = MagicMock(return_value="Permissions revoked successfully.")
        
        # Test parameters
        parameters = {
            "token": "USDC", 
            "protocol": "Compromised Protocol",
            "chain_id": "84532"
        }
        
        # Execute the revoke tool
        print("\nRevoke Tool Test:")
        print("-" * 50)
        result = security_agent.revoke_tool(parameters)
        print(result)
        print("-" * 50)
        
        # Assert that revoke_tool was called with the correct parameters
        security_agent.revoke_tool.assert_called_once_with(parameters)
        self.assertEqual(result, "Permissions revoked successfully.")

    @patch('os.path.exists')
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{}')
    @patch('json.load', return_value={})
    def test_monitor_tool(self, mock_json_load, mock_open, mock_path_exists):
        """
        Test the monitor tool directly.
        """
        # Set up mock for json.load to return specific data for each file
        mock_path_exists.return_value = True
        mock_json_load.side_effect = [
            {"dependencies": []},  # dependency_graph
            {"users": []},         # user_balances
            {"tokens": []},        # tokens_config
            {"protocols": []}      # protocols_config
        ]
        
        # Mock OpenAI client
        mock_openai = MagicMock()
        
        # Create security agent
        security_agent = SecurityAgent(mock_openai)
        
        # Mock the monitor tool
        security_agent.monitor_tool = MagicMock(return_value="Monitoring set up successfully.")
        
        # Test parameters
        parameters = {
            "asset": "All Base Chain Positions", 
            "duration": "48h"
        }
        
        # Execute the monitor tool
        print("\nMonitor Tool Test:")
        print("-" * 50)
        result = security_agent.monitor_tool(parameters)
        print(result)
        print("-" * 50)
        
        # Assert that monitor_tool was called with the correct parameters
        security_agent.monitor_tool.assert_called_once_with(parameters)
        self.assertEqual(result, "Monitoring set up successfully.")

# Run the test
if __name__ == "__main__":
    unittest.main()
