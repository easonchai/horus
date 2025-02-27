"""
Security agent for the Horus security monitoring system.
Class-based implementation.
"""
import json
import logging
import os
import re
from typing import Any, Callable, Dict, List, Optional, Tuple

from horus.tools import create_monitor_tool
from horus.tools.revoke import RevokeTool
from horus.tools.withdrawal import WithdrawalTool

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')
logger = logging.getLogger(__name__)


class SecurityAgent:
    """
    Security agent that processes security alerts and takes appropriate actions.
    
    The SecurityAgent monitors for security threats and can respond with actions such as:
    - Withdrawing funds to a safe address
    - Revoking token permissions
    - Setting up monitoring for specific assets
    
    It uses AI to determine the appropriate response to security alerts.
    """
    
    def __init__(self, openai_client, mock_openai=False, mock_twitter=True):
        """
        Initialize the security agent.
        
        Args:
            openai_client: The OpenAI client.
            mock_openai: Whether to mock OpenAI responses.
            mock_twitter: Whether to mock Twitter responses.
        """
        self.openai_client = openai_client
        self.mock_openai = mock_openai
        self.mock_twitter = mock_twitter
        
        # Load configuration files
        self.dependency_graph = self._load_dependency_graph()
        self.user_balances = self._load_user_balances()
        self.tokens_config = self._load_tokens_config()
        self.protocols_config = self._load_protocols_config()
        
        # Initialize tools
        self.withdrawal_tool = WithdrawalTool(self.dependency_graph, self.user_balances, self.protocols_config)
        self.revoke_tool = RevokeTool(self.tokens_config, self.protocols_config)
        self.monitor_tool = create_monitor_tool()
    
    def __call__(self, alert_text: str) -> str:
        """
        Process a security alert and take appropriate action.
        
        This makes the instance callable, maintaining compatibility with the functional approach.
        
        Args:
            alert_text: The text of the security alert.
            
        Returns:
            A string describing the action taken.
        """
        return self.process_alert(alert_text)
    
    # Configuration loading methods
    def _load_dependency_graph(self) -> Dict[str, Any]:
        """
        Load the dependency graph from the configuration file.
        
        Returns:
            Dictionary containing the dependency graph data.
        """
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            graph_path = os.path.join(base_path, '..', '..', 'config', 'dependency_graph.json')
            
            with open(graph_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading dependency graph: {str(e)}")
            return {"dependencies": []}
    
    def _load_user_balances(self) -> Dict[str, Any]:
        """
        Load user balances from the data file.
        
        Returns:
            Dictionary containing user balance data.
        """
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            balances_path = os.path.join(base_path, '..', '..', 'user_data', 'user_balances.json')
            
            with open(balances_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading user balances: {str(e)}")
            return {"users": []}
    
    def _load_tokens_config(self) -> Dict[str, Any]:
        """
        Load token configuration from the config file.
        
        Returns:
            Dictionary containing token configuration data.
        """
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            tokens_path = os.path.join(base_path, '..', '..', 'config', 'tokens.json')
            
            with open(tokens_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading tokens config: {str(e)}")
            return {"tokens": []}
    
    def _load_protocols_config(self) -> Dict[str, Any]:
        """
        Load protocols configuration from the config file.
        
        Returns:
            Dictionary containing protocols configuration data.
        """
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            protocols_path = os.path.join(base_path, '..', '..', 'config', 'protocols.json')
            
            with open(protocols_path, 'r') as file:
                return json.load(file)
        except Exception as e:
            logger.error(f"Error loading protocols config: {str(e)}")
            return {"protocols": []}
    
    # Helper methods for data access
    def get_user_positions(self, user_address: str, chain_id: str) -> List[Dict[str, Any]]:
        """
        Get positions for a user on a specific chain.
        
        Args:
            user_address: The user's address.
            chain_id: The chain ID.
            
        Returns:
            A list of user positions.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        if not self.user_balances:
            logger.warning("User balances not loaded")
            return []
        
        user_data = self.user_balances.get(user_address, {})
        chain_data = user_data.get(chain_id, {})
        return chain_data.get("positions", [])
    
    def get_exit_functions_for_token(self, token: str, chain_id: str) -> List[Dict[str, Any]]:
        """
        Get exit functions for a token on a specific chain.
        
        Args:
            token: The token symbol.
            chain_id: The chain ID.
            
        Returns:
            A list of exit functions.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        if not self.dependency_graph:
            logger.warning("Dependency graph not loaded")
            return []
        
        # Find the token in the dependency graph
        for node in self.dependency_graph.get("nodes", []):
            if node.get("symbol") == token and str(node.get("chainId")) == chain_id:
                return node.get("exitFunctions", [])
        
        return []
    
    def get_token_address(self, token_symbol: str, chain_id: str) -> Optional[str]:
        """
        Get the contract address for a token on a specific chain.
        
        Args:
            token_symbol: The symbol of the token.
            chain_id: The chain ID.
            
        Returns:
            Token contract address or None if not found.
        """
        chain_id = str(chain_id)  # Ensure chain_id is a string
        
        for token in self.tokens_config.get("tokens", []):
            if token.get("symbol") == token_symbol:
                networks = token.get("networks", {})
                return networks.get(chain_id)
        return None
    
    def get_token_dependencies(self, token_symbol: str) -> List[Dict[str, Any]]:
        """
        Get dependencies for a specific token.
        
        Args:
            token_symbol: The symbol of the token.
            
        Returns:
            List of underlying tokens and their information.
        """
        for dependency in self.dependency_graph.get("dependencies", []):
            if dependency.get("derivativeSymbol") == token_symbol:
                return dependency.get("underlyings", [])
        return []
    
    # AI interaction methods
    def prepare_context_for_ai(self) -> str:
        """
        Prepare context information from dependency graph and user balances for the AI.
        
        Returns:
            A string containing formatted context information.
        """
        context = []
        
        # Add information about dependencies
        context.append("DEPENDENCY INFORMATION:")
        for dependency in self.dependency_graph.get("dependencies", [])[:5]:  # Limit to prevent token overflow
            derivative = dependency.get("derivativeSymbol", "unknown")
            protocol = dependency.get("protocol", "unknown")
            chain = dependency.get("chainId", "unknown")
            underlyings = dependency.get("underlyings", [])
            
            underlying_info = []
            for u in underlyings:
                if isinstance(u, dict):
                    underlying_info.append(f"{u.get('symbol', 'unknown')} (ratio: {u.get('ratio', 'unknown')})")
                else:
                    underlying_info.append(str(u))
            
            context.append(f"- {derivative} on {protocol} (Chain: {chain}) is based on: {', '.join(underlying_info)}")
        
        # Add user balance information
        context.append("\nUSER BALANCE INFORMATION:")
        for user in self.user_balances.get("users", []):
            address = user.get("address", "unknown")
            context.append(f"- User: {address}")
            
            for chain_id, balances in user.get("chainBalances", {}).items():
                context.append(f"  Chain {chain_id}:")
                
                # Add token balances
                for token, amount in balances.items():
                    if token != "positions":
                        context.append(f"  - {token}: {amount}")
                
                # Add positions
                if "positions" in balances:
                    context.append(f"  Positions:")
                    for position in balances["positions"]:
                        protocol = position.get("protocol", "")
                        symbol = position.get("symbol", "unknown")
                        token_id = position.get("tokenId", "unknown")
                        shares = position.get("shares", "")
                        liquidity = position.get("liquidity", "")
                        
                        position_info = f"  - {symbol} (ID: {token_id})"
                        if protocol:
                            position_info += f" on {protocol}"
                        if shares:
                            position_info += f", Shares: {shares}"
                        if liquidity:
                            position_info += f", Liquidity: {liquidity}"
                            
                        context.append(position_info)
        
        return "\n".join(context)
    
    def _extract_parameter(self, text: str, param_name: str, default_value: str) -> str:
        """
        Extract a parameter value from text.
        
        Args:
            text: The text to extract from.
            param_name: The name of the parameter.
            default_value: The default value if the parameter is not found.
            
        Returns:
            The extracted parameter value or the default value.
        """
        # Try to find the parameter in the text
        pattern = rf'{param_name}["\s:]+([^",\s]+|"[^"]+"|\'[^\']+\')'
        match = re.search(pattern, text, re.IGNORECASE)
        
        if match:
            value = match.group(1).strip('"\'')
            return value
            
        return default_value
    
    def _get_default_monitor_action(self) -> Tuple[str, Dict[str, Any]]:
        """
        Get the default monitoring action parameters.
        
        Returns:
            A tuple of ("monitor", default_parameters).
        """
        parameters = {
            "asset": "All Positions",
            "duration": "24h",
            "threshold": "5%"
        }
        return "monitor", parameters
    
    def try_parse_json_response(self, response_text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Attempt to parse the response as JSON with an action_plan structure.
        
        Args:
            response_text: The response from the AI.
            
        Returns:
            A tuple of (action_type, parameters) if successful, None otherwise.
        """
        try:
            response_json = json.loads(response_text)
            
            # If the response is a JSON object with an action_plan field
            if "action_plan" in response_json and isinstance(response_json["action_plan"], list):
                # Take the first action in the plan
                if response_json["action_plan"]:
                    action = response_json["action_plan"][0]
                    return action.get("action", "unknown"), action.get("parameters", {})
            
            # If we got here, JSON was valid but didn't have the expected structure
            return None
        except json.JSONDecodeError:
            # Not valid JSON
            return None
    
    def _parse_text_response(self, response_text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse the response as plain text, looking for keywords and extracting parameters.
        
        Args:
            response_text: The response from the AI.
            
        Returns:
            A tuple containing the action type and parameters.
        """
        response_lower = response_text.lower()
        
        # Check for withdrawal action
        if "withdraw" in response_lower or "exit" in response_lower:
            token = self._extract_parameter(response_text, "token", "unknown")
            amount = self._extract_parameter(response_text, "amount", "all")
            chain_id = self._extract_parameter(response_text, "chain_id", "1")
            
            return "withdrawal", {
                "token": token,
                "amount": amount,
                "chain_id": chain_id
            }
        
        # Check for revoke action
        elif "revoke" in response_lower or "permissions" in response_lower or "approval" in response_lower:
            token = self._extract_parameter(response_text, "token", "unknown")
            token_address = self._extract_parameter(response_text, "token_address", "unknown")
            protocol = self._extract_parameter(response_text, "protocol", "unknown")
            chain_id = self._extract_parameter(response_text, "chain_id", "1")
            spender_address = self._extract_parameter(response_text, "spender_address", "")
            
            return "revoke", {
                "token": token,
                "token_address": token_address,
                "protocol": protocol,
                "chain_id": chain_id,
                "spender_address": spender_address
            }
        
        # Default to monitor action
        else:
            return self._get_default_monitor_action()
    
    def parse_ai_response(self, response_text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse the AI response to determine the action to take.
        
        This method attempts to parse the response in two ways:
        1. First as a structured JSON with an action_plan field
        2. If that fails, falls back to text-based keyword parsing
        
        Args:
            response_text: The response from the AI.
            
        Returns:
            A tuple containing the action type and parameters.
        """
        logger.info("Parsing AI response")
        
        try:
            # First try to parse as JSON
            json_result = self.try_parse_json_response(response_text)
            if json_result:
                return json_result
            
            # If JSON parsing fails or doesn't match expected format, 
            # fall back to text parsing
            return self._parse_text_response(response_text)
                
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            # Default to monitoring in case of error
            return self._get_default_monitor_action()
    
    def get_mock_response(self, alert_text: str) -> str:
        """
        Generate a mock response for testing purposes.
        
        Args:
            alert_text: The text of the security alert.
            
        Returns:
            A string describing the action taken.
        """
        logger.info("Generating mock response")
        
        # Extract keywords from the alert text to determine the appropriate action
        alert_lower = alert_text.lower()
        
        if "withdraw" in alert_lower or "vulnerability" in alert_lower:
            parameters = {
                "token": "USDC",
                "amount": "ALL",
                "destination": "safe_wallet",
                "chain_id": "84532",  # Base chain
                "user_address": "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266"
            }
            return self.withdrawal_tool(parameters)
            
        elif "revoke" in alert_lower or "permissions" in alert_lower:
            parameters = {
                "token": "USDC",
                "protocol": "Compromised Protocol",
                "chain_id": "84532"  # Base chain
            }
            return self.revoke_tool(parameters)
            
        else:
            parameters = {
                "asset": "All Base Chain Positions",
                "duration": "48h",
                "threshold": "3%"
            }
            return self.monitor_tool(parameters)
    
    def process_alert(self, alert_text: str) -> str:
        """
        Process a security alert and take appropriate action.
        
        Args:
            alert_text: The text of the security alert.
            
        Returns:
            A string describing the action taken.
        """
        # Prepare the context for the AI
        context = self.prepare_context_for_ai()
        
        # If we're mocking OpenAI, return a mock response
        if self.mock_openai:
            logger.info("Using mock OpenAI response")
            return self.get_mock_response(alert_text)
        
        # Otherwise, use the OpenAI API to process the alert
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": f"SECURITY ALERT: {alert_text}"}
                ],
                temperature=0.2,
            )
            
            # Extract the response text
            response_text = response.choices[0].message.content
            logger.info(f"OpenAI response: {response_text}")
            
            # Parse the response to determine the action to take
            action_type, parameters = self.parse_ai_response(response_text)
            
            # Take the appropriate action
            if action_type == "withdrawal":
                return self.withdrawal_tool(parameters)
            elif action_type == "revoke":
                return self.revoke_tool(parameters)
            elif action_type == "monitor":
                return self.monitor_tool(parameters)
            else:
                return f"No action taken. AI response: {response_text}"
            
        except Exception as e:
            logger.error(f"Error processing security alert: {e}")
            return f"Error processing security alert: {e}"
    
    # Compatibility methods for backward compatibility
    def process_security_alert(self, alert_text: str) -> str:
        """Alias for process_alert for backward compatibility."""
        return self.process_alert(alert_text)
    
    def _prepare_context_for_ai(self) -> str:
        """Alias for prepare_context_for_ai for backward compatibility."""
        return self.prepare_context_for_ai()
    
    def _parse_ai_response(self, response_text: str) -> Tuple[str, Dict[str, Any]]:
        """Alias for parse_ai_response for backward compatibility."""
        return self.parse_ai_response(response_text)
    
    def _get_mock_response(self, alert_text: str) -> str:
        """Alias for get_mock_response for backward compatibility."""
        return self.get_mock_response(alert_text)
    
    def _try_parse_json_response(self, response_text: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """Alias for try_parse_json_response for backward compatibility."""
        return self.try_parse_json_response(response_text)
