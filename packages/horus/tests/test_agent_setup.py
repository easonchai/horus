import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the horus module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from horus.agent_setup import setup_agent


class TestAgentSetup(unittest.TestCase):
    """Test the agent setup functionality."""

    @patch('horus.agent_setup.os.getenv')
    @patch('horus.agent_setup.OpenAI')
    def test_setup_agent_with_env_vars(self, mock_openai, mock_getenv):
        """Test that the agent setup works when environment variables are set."""
        # Mock environment variables
        mock_getenv.side_effect = lambda key: {
            'CDP_API_KEY_NAME': 'test_key_name',
            'CDP_API_KEY_PRIVATE_KEY': 'test_private_key',
            'OPENAI_API_KEY': 'test_openai_key'
        }.get(key)

        # Mock OpenAI client
        mock_openai_instance = MagicMock()
        mock_openai.return_value = mock_openai_instance

        # Mock the imported modules
        mock_agent_kit = MagicMock()
        mock_agent_kit_instance = MagicMock()
        mock_agent_kit.return_value = mock_agent_kit_instance

        mock_cdp_toolkit = MagicMock()
        mock_cdp_toolkit_instance = MagicMock()
        mock_cdp_toolkit.return_value = mock_cdp_toolkit_instance
        mock_cdp_toolkit_instance.get_tools.return_value = []

        mock_agent_executor = MagicMock()
        mock_create_openai_tools_agent = MagicMock()

        # Create mock modules
        mock_modules = {
            'coinbase_agentkit': MagicMock(AgentKit=mock_agent_kit),
            'coinbase_agentkit_langchain': MagicMock(CDPToolkit=mock_cdp_toolkit),
            'langchain.agents': MagicMock(
                AgentExecutor=mock_agent_executor,
                create_openai_tools_agent=mock_create_openai_tools_agent
            ),
            'langchain.prompts': MagicMock(),
            'langchain.memory': MagicMock(),
            'langchain.schema.messages': MagicMock(),
        }
        
        with patch.dict('sys.modules', mock_modules):
            # Call the function
            result = setup_agent()

            # Assertions
            self.assertIsNotNone(result)
            mock_openai.assert_called_once_with(api_key='test_openai_key')

    @patch('horus.agent_setup.os.getenv')
    @patch('horus.agent_setup.print')
    def test_setup_agent_missing_env_vars(self, mock_print, mock_getenv):
        """Test that the agent setup fails when environment variables are missing."""
        # Mock missing environment variables
        mock_getenv.return_value = None

        # Call the function
        result = setup_agent()

        # Assertions
        self.assertIsNone(result)
        mock_print.assert_called()


if __name__ == '__main__':
    unittest.main() 