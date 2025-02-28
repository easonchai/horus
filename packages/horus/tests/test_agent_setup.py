import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the horus module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_setup import setup_agent


class TestAgentSetup(unittest.TestCase):
    """Test the agent setup functionality."""

    @patch('horus.agent_setup.os.getenv')
    @patch('horus.agent_setup.OpenAI')
    @patch('horus.agent_setup.agent_kit_manager.initialize_agentkit')
    def test_setup_agent_with_env_vars(self, mock_initialize_agentkit, mock_openai, mock_getenv):
        """Test that the agent setup works when environment variables are set."""
        # Mock environment variables
        mock_getenv.side_effect = lambda key: {
            'OPENAI_API_KEY': 'test_openai_key'
        }.get(key)

        # Mock OpenAI client
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance

        # Mock agent_kit_manager.initialize_agentkit response
        mock_initialize_agentkit.return_value = {
            'wallet_provider': MagicMock(),
            'action_provider': MagicMock(),
            'wallet_address': '0x1234567890123456789012345678901234567890',
            'agentkit': MagicMock()
        }

        # Call the function
        result = setup_agent()

        # Assertions
        self.assertIsNotNone(result)
        mock_openai.assert_called_once_with(api_key='test_openai_key')
        mock_initialize_agentkit.assert_called_once()
        
        # Check that the result contains the expected components
        self.assertIn('openai_client', result)
        self.assertIn('agent_kit', result)
        self.assertIn('wallet_provider', result)
        self.assertIn('action_provider', result)
        self.assertIn('wallet_address', result)

    @patch('horus.agent_setup.os.getenv')
    @patch('horus.agent_setup.logger')
    def test_setup_agent_missing_env_vars(self, mock_logger, mock_getenv):
        """Test that the agent setup fails when environment variables are missing."""
        # Mock missing environment variables
        mock_getenv.return_value = None

        # Call the function
        result = setup_agent()

        # Assertions
        self.assertIsNone(result)
        mock_logger.error.assert_called()
        mock_logger.warning.assert_called()

    @patch('horus.agent_setup.os.getenv')
    @patch('horus.agent_setup.OpenAI')
    @patch('horus.agent_setup.agent_kit_manager.initialize_agentkit')
    @patch('horus.agent_setup.logger')
    def test_setup_agent_exception_handling(self, mock_logger, mock_initialize_agentkit, mock_openai, mock_getenv):
        """Test that the agent setup handles exceptions properly."""
        # Mock environment variables
        mock_getenv.return_value = 'test_openai_key'
        
        # Mock exception in initialize_agentkit
        mock_initialize_agentkit.side_effect = Exception("Test exception")
        
        # Call the function
        result = setup_agent()
        
        # Assertions
        self.assertIsNone(result)
        mock_logger.error.assert_called_with("Error setting up agent: Test exception")


if __name__ == '__main__':
    unittest.main() 