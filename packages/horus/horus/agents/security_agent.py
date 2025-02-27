"""
Security agent for the Horus security monitoring system.
Functional programming implementation.
"""
import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

from horus.agents.security_agent_functional import (
    create_security_agent as create_security_agent_func,
    get_user_positions, get_exit_functions_for_token,
    get_token_address, get_token_dependencies
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)

# Create a factory function that maintains compatibility with the class-based API
def SecurityAgent(openai_client, mock_openai=False, mock_twitter=True):
    """
    Factory function that creates a security agent with the same API as the original class.
    
    Args:
        openai_client: The OpenAI client.
        mock_openai: Whether to mock OpenAI responses.
        mock_twitter: Whether to mock Twitter responses.
        
    Returns:
        A security agent function with attached methods to maintain compatibility.
    """
    # Create the base security agent function
    agent = create_security_agent_func(openai_client, mock_openai, mock_twitter)
    
    # The agent already has the following attributes attached:
    # - dependency_graph
    # - user_balances
    # - tokens_config
    # - withdrawal_tool
    # - revoke_tool
    # - monitor_tool
    # - get_user_positions (as a lambda)
    # - get_exit_functions_for_token (as a lambda)
    # - get_token_address (as a lambda)
    # - get_token_dependencies (as a lambda)
    
    # Add _prepare_context_for_ai method for compatibility
    agent._prepare_context_for_ai = lambda: agent.prepare_context_for_ai(
        agent.dependency_graph, agent.user_balances
    )
    
    # Add _parse_ai_response method for compatibility
    agent._parse_ai_response = lambda response_text: agent.parse_ai_response(response_text)
    
    # Add _get_mock_response method for compatibility
    agent._get_mock_response = lambda alert_text: agent.get_mock_response(
        alert_text, agent.withdrawal_tool, agent.revoke_tool, agent.monitor_tool
    )
    
    # Add _try_parse_json_response method for compatibility
    agent._try_parse_json_response = lambda response_text: agent.try_parse_json_response(response_text)
    
    # Add process_security_alert method for compatibility
    agent.process_security_alert = lambda alert_text: agent.process_alert(alert_text)
    
    return agent
